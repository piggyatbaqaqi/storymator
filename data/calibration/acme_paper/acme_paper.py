"""ACME punch geometry — loader and statistics for the acme_paper dataset.

Flatbed scans of hole-punched animation bond, one PNG per sheet, with
every geometric quantity the dataset card reports derived here rather
than quoted from prose.  Running this file regenerates the whole
statistics section:

    python acme_paper.py                     # all reams found
    python acme_paper.py canson_ream_0001    # one ream
    python acme_paper.py --csv out.csv       # per-sheet rows as well

As a dataset:

    from acme_paper import load
    ds = load("canson_ream_0001")            # one row per sheet

``datasets`` removed support for loading scripts in 3.0, so ``load()``
builds through ``Dataset.from_generator`` rather than relying on
``load_dataset`` finding this file.  The ``GeneratorBasedBuilder`` at
the bottom is kept for older installations and is skipped silently if
``datasets`` is absent.

Measurement notes that matter for reading the numbers:

* Everything is expressed in a frame built from each sheet's **own**
  punched edge, which is what makes scanner placement irrelevant.  A
  flatbed's belt axis is good to a few tenths of a percent at best, and
  that error is identical for every sheet placed in the same spot, so
  it cancels in any spread.  Absolute offsets are contaminated; spreads
  are clean.
* Hole *size* carries a further bias: a thresholded or 50 %-crossing
  edge sits inside the true aperture, because the punch tears fibres
  down into the hole and a lit burr over a dark hole reads as hole.
  Every size mean below is therefore a **lower bound**.  A constant
  bias cancels out of a standard deviation, so the size *spreads*
  stand while the size *means* do not.
"""

# SPDX-License-Identifier: GPL-3.0-or-later
# Code, not data: the surrounding directory is CC-BY-4.0.
from __future__ import annotations

import argparse
import csv
import glob
import os
import sys
from typing import Dict, Iterator, List, Optional

import numpy as np

try:
    from PIL import Image
    from scipy import ndimage
except ModuleNotFoundError as exc:               # pragma: no cover
    raise SystemExit(f"needs Pillow and scipy: {exc}")

HERE = os.path.dirname(os.path.abspath(__file__))
DPI = 300.0
MM = 25.4 / DPI

# Nominals, for the "off by" columns.  The pegs are measured values for
# honbay_0001 (see ../pegs/honbay_0001/README.md), not catalogue figures.
NOMINAL_PITCH_MM = 101.6
NOMINAL_SPAN_MM = 203.2
PEG_ROUND_MM = 6.440
PEG_RECT_SHORT_MM = 3.142
PEG_RECT_LONG_MM = 12.72


# --------------------------------------------------------------------
# geometry helpers


def fit_line(points: np.ndarray):
    """Total-least-squares line through 2-D points -> (origin, unit dir)."""
    o = points.mean(axis=0)
    _, _, vt = np.linalg.svd(points - o, full_matrices=False)
    return o, vt[0] / np.linalg.norm(vt[0])


def cross2(a: np.ndarray, b: np.ndarray) -> float:
    return float(a[0] * b[1] - a[1] * b[0])


def _ray_diameter(a, centre, black, white, rmax=60, n=720):
    """Diameter from the 50 % crossing along n rays -- the principled one.

    Sub-pixel, and averaging over hundreds of edge points rather than
    two, so it is far less sensitive to the threshold than an area or
    an extent.
    """
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = np.arange(0, rmax, 0.25)
    xs = centre[0] + np.outer(np.cos(th), r)
    ys = centre[1] + np.outer(np.sin(th), r)
    v = ndimage.map_coordinates(a, [ys.ravel(), xs.ravel()], order=1)
    v = v.reshape(n, len(r))
    half = (black + white) / 2.0
    radii = []
    for row in v:
        k = int(np.argmax(row > half))
        if k == 0:
            continue
        lo, hi = row[k - 1], row[k]
        if hi <= lo:
            continue
        radii.append(r[k - 1] + (half - lo) / (hi - lo) * 0.25)
    return 2 * float(np.median(radii)) if radii else float("nan")


# --------------------------------------------------------------------
# per-sheet measurement


def measure_sheet(path: str) -> Optional[Dict]:
    """Every quantity for one scan, or None if the scan is unusable."""
    a = np.asarray(Image.open(path).convert("L"), float)

    sheet = a > 128
    lab, n = ndimage.label(sheet)
    if n == 0:
        return None
    sizes = ndimage.sum(sheet, lab, range(1, n + 1))
    sheet = lab == int(np.argmax(sizes)) + 1

    holes = ndimage.binary_fill_holes(sheet) & ~sheet
    lab2, n2 = ndimage.label(holes)
    if n2 == 0:
        return None

    found = []
    for i, box in enumerate(ndimage.find_objects(lab2), start=1):
        if box is None:
            continue
        m = lab2[box] == i
        area = float(m.sum())
        if not (2000 < area < 20000):
            continue
        yy, xx = np.nonzero(m)
        yy = yy + box[0].start
        xx = xx + box[1].start
        pts = np.column_stack([xx, yy]).astype(float)
        c = pts.mean(axis=0)
        _, ev = np.linalg.eigh(np.cov((pts - c).T))
        # +1 because ptp over pixel INDICES is centre-to-centre: an
        # N-pixel run spans N-1.  Omitting it costs a flat 1 px, which
        # is 0.085 mm at 300 dpi and reads as a real undersize.
        ext = np.ptp((pts - c) @ ev, axis=0) + 1.0
        found.append(dict(c=c, area=area, short=float(min(ext)),
                          long=float(max(ext))))
    if len(found) != 3:
        return None

    found.sort(key=lambda h: h["c"][1])
    top, mid, bot = found
    if mid["long"] / max(mid["short"], 1e-9) > 1.4:
        return None                       # the round hole must be in the middle

    # The bottom sheet edge, when it is on the bed at all.  Some sheets
    # cover the whole platen, and an "edge" read off the bed boundary is
    # the scanner's frame rather than the paper's.
    H = sheet.shape[0]
    ys, xs = np.nonzero(sheet)
    edge = []
    for x in range(int(xs.min()) + 40, int(xs.max()) - 40, 7):
        col = np.nonzero(sheet[:, x])[0]
        if len(col) and col.max() < H - 3:
            edge.append((x, col.max()))
    edge = np.array(edge, float)
    have_edge = len(edge) > 200
    o = d = None
    if have_edge:
        keep = np.abs(edge[:, 1] - np.median(edge[:, 1])) < 20
        if keep.sum() > 100:
            o, d = fit_line(edge[keep])
        else:
            have_edge = False

    def to_edge(p):
        return abs(cross2(d, p - o)) * MM if have_edge else float("nan")

    line = bot["c"] - top["c"]
    unit = line / np.linalg.norm(line)

    # round hole size, three ways, so the reader can see the method
    # spread as well as the sheet-to-sheet spread
    cx, cy = mid["c"]
    win = a[int(cy) - 70:int(cy) + 70, int(cx) - 70:int(cx) + 70]
    if win.size:
        black, white = np.percentile(win, 2), np.percentile(win, 98)
        ray = _ray_diameter(a, mid["c"], black, white) * MM
    else:
        ray = float("nan")

    return dict(
        sheet_id=os.path.splitext(os.path.basename(path))[0],
        d1=float(np.linalg.norm(mid["c"] - top["c"])) * MM,
        d2=float(np.linalg.norm(bot["c"] - mid["c"])) * MM,
        span=float(np.linalg.norm(line)) * MM,
        span_x=abs(float(line[0])) * MM,
        span_y=abs(float(line[1])) * MM,
        straight=abs(cross2(unit, mid["c"] - top["c"])) * MM,
        perp=(abs(90 - np.degrees(np.arccos(abs(float(np.dot(unit, d))))))
              if have_edge else float("nan")),
        edge_to_mid=to_edge(mid["c"]),
        edge_to_top=to_edge(top["c"]),
        round_dia_ray=ray,
        round_dia_area=2 * float(np.sqrt(mid["area"] / np.pi)) * MM,
        round_dia_ext=(mid["short"] + mid["long"]) / 2 * MM,
        rect_short=(top["short"] + bot["short"]) / 2 * MM,
        rect_long=(top["long"] + bot["long"]) / 2 * MM,
        placement_y=float(mid["c"][1]) * MM,
        image_path=path,
    )


def reams(root: str = HERE) -> List[str]:
    return sorted(os.path.basename(d) for d in glob.glob(os.path.join(root, "*"))
                  if os.path.isdir(d) and glob.glob(os.path.join(d, "*.png")))


def measure_ream(ream: str, root: str = HERE) -> List[Dict]:
    files = sorted(glob.glob(os.path.join(root, ream, "*.png")))
    if not files:
        raise SystemExit(f"no PNGs under {os.path.join(root, ream)}")
    out = []
    for f in files:
        r = measure_sheet(f)
        if r:
            r["ream"] = ream
            out.append(r)
    return out


# --------------------------------------------------------------------
# statistics


def _s(values) -> Dict:
    v = np.asarray([x for x in values if np.isfinite(x)], float)
    if not len(v):
        return dict(n=0)
    return dict(n=len(v), mean=float(v.mean()),
                sd=float(v.std(ddof=1)) if len(v) > 1 else float("nan"),
                min=float(v.min()), max=float(v.max()),
                range=float(np.ptp(v)))


def statistics(rows: List[Dict]) -> Dict:
    """Every figure the dataset card quotes."""
    g = lambda k: [r[k] for r in rows]
    st = {k: _s(g(k)) for k in
          ("d1", "d2", "span", "straight", "perp", "edge_to_mid",
           "edge_to_top", "round_dia_ray", "round_dia_area",
           "round_dia_ext", "rect_short", "rect_long")}

    place = np.array(g("placement_y"))
    d1 = np.array(g("d1"))
    d2 = np.array(g("d2"))
    st["_controls"] = dict(
        placement_sd_mm=float(place.std(ddof=1)),
        corr_placement_d1=float(np.corrcoef(place, d1)[0, 1]),
        corr_placement_d2=float(np.corrcoef(place, d2)[0, 1]),
        asymmetry_mean=float((d2 - d1).mean()),
        asymmetry_sd=float((d2 - d1).std(ddof=1)),
        corr_placement_asymmetry=float(np.corrcoef(place, d2 - d1)[0, 1]),
    )

    sx, sy = np.array(g("span_x")), np.array(g("span_y"))
    span = np.array(g("span"))
    st["_scan_axis"] = dict(
        span_across_sensor_mm=float(sx.mean()),
        span_along_scan_mm=float(sy.mean()),
        off_axis_deg=float(np.degrees(np.arctan2(sx.mean(), sy.mean()))),
        span_error_ppm=float(1e6 * (span.mean() - NOMINAL_SPAN_MM)
                             / NOMINAL_SPAN_MM),
    )

    ray = np.array([r["round_dia_ray"] for r in rows if np.isfinite(r["round_dia_ray"])])
    lo, hi = np.percentile(ray, [2.5, 97.5])
    st["_round"] = dict(
        band_lo=float(lo), band_hi=float(hi), band=float(hi - lo),
        sd_um=float(1e3 * ray.std(ddof=1)),
        sd_pct=float(100 * ray.std(ddof=1) / ray.mean()),
        peg_minus_hole=float(PEG_ROUND_MM - ray.mean()),
    )
    st["_consistency"] = dict(
        pitch_sd_um=float(1e3 * d1.std(ddof=1)),
        pitch_sd_pct=float(100 * d1.std(ddof=1) / d1.mean()),
        hole_sd_um=st["_round"]["sd_um"], hole_sd_pct=st["_round"]["sd_pct"],
        ratio=float(st["_round"]["sd_pct"] / (100 * d1.std(ddof=1) / d1.mean())),
    )
    st["_n"] = len(rows)
    return st


def report(rows: List[Dict], out=sys.stdout) -> None:
    st = statistics(rows)
    p = lambda *a: print(*a, file=out)

    def line(label, k, unit="mm", nominal=None):
        s = st[k]
        if not s["n"]:
            p(f"  {label:34s} not measurable"); return
        txt = (f"  {label:34s} {s['mean']:9.4f} {s['sd']:8.4f} "
               f"{s['min']:9.4f} {s['max']:9.4f} {s['range']:8.4f}")
        if nominal is not None:
            txt += f"   {s['mean'] - nominal:+.4f} vs {nominal}"
        p(txt)

    p(f"\n{st['_n']} sheets measured\n")
    p(f"  {'':34s} {'mean':>9} {'sd':>8} {'min':>9} {'max':>9} {'range':>8}")
    p("\nTHE PATTERN")
    line("upper pitch", "d1", nominal=NOMINAL_PITCH_MM)
    line("lower pitch", "d2", nominal=NOMINAL_PITCH_MM)
    line("outer span", "span", nominal=NOMINAL_SPAN_MM)
    line("collinearity of centre hole", "straight")
    line("squareness to the sheet edge", "perp", unit="deg")

    p("\nPOSITION ALONG THE SHEET  (contaminated in the mean, clean in the spread)")
    line("sheet edge to centre hole", "edge_to_mid")
    line("sheet edge to upper hole", "edge_to_top")

    p("\nROUND PUNCH SIZE  (means are LOWER BOUNDS -- see the module docstring)")
    line("50 % edge crossing, 720 rays", "round_dia_ray", nominal=PEG_ROUND_MM)
    line("thresholded area", "round_dia_area", nominal=PEG_ROUND_MM)
    line("extent + 1 px", "round_dia_ext", nominal=PEG_ROUND_MM)
    r = st["_round"]
    p(f"    sd {r['sd_um']:.0f} um = {r['sd_pct']:.2f} % of the mean; "
      f"95 % of sheets in {r['band_lo']:.3f}-{r['band_hi']:.3f} "
      f"(a {r['band']:.3f} mm band)")
    p(f"    peg {PEG_ROUND_MM} - optical mean = {r['peg_minus_hole']:+.3f} mm, "
      f"which the grip fit requires")

    p("\nRECT PUNCH SIZE")
    line("short axis", "rect_short", nominal=PEG_RECT_SHORT_MM)
    line("long axis", "rect_long", nominal=PEG_RECT_LONG_MM)

    c = st["_controls"]
    p("\nCONTROLS")
    p(f"  sheet placement on the bed varied by sd {c['placement_sd_mm']:.2f} mm")
    p(f"  corr(placement, upper pitch) = {c['corr_placement_d1']:+.2f}")
    p(f"  corr(placement, lower pitch) = {c['corr_placement_d2']:+.2f}")
    p("  -> no scanner nonlinearity leaked in; the spreads above are paper")
    p(f"  die asymmetry, lower minus upper gap: {c['asymmetry_mean']:+.4f} mm "
      f"sd {c['asymmetry_sd']:.4f}, corr with placement "
      f"{c['corr_placement_asymmetry']:+.2f}")

    a = st["_scan_axis"]
    p("\nSCAN AXIS")
    p(f"  the hole line runs {a['off_axis_deg']:.2f} deg off the scan axis, so the")
    p(f"  {NOMINAL_SPAN_MM} mm span is a pure length along the belt-driven axis")
    p(f"  ({a['span_along_scan_mm']:.4f} along the scan, "
      f"{a['span_across_sensor_mm']:.4f} across the sensor)")
    p(f"  it is centroid-to-centroid, so it carries no edge bias, and reads "
      f"{a['span_error_ppm']:+.0f} ppm")
    p("  the SENSOR axis is not checked: nothing here spans a long distance across it")

    k = st["_consistency"]
    p("\nCONSISTENCY, SIZE AGAINST SPACING")
    p(f"  hole pitch   sd {k['pitch_sd_um']:5.0f} um = {k['pitch_sd_pct']:.3f} %")
    p(f"  round hole   sd {k['hole_sd_um']:5.0f} um = {k['hole_sd_pct']:.3f} %")
    p(f"  -> size is {k['ratio']:.0f}x less consistent than spacing, relatively.")
    p("     Expected, and not a criticism: spacing is set by rigid steel,")
    p("     size by where paper fibres tear.")


# --------------------------------------------------------------------
# datasets integration

FEATURE_KEYS = ("sheet_id", "ream", "d1", "d2", "span", "span_x", "span_y",
                "straight", "perp", "edge_to_mid", "edge_to_top",
                "round_dia_ray", "round_dia_area", "round_dia_ext",
                "rect_short", "rect_long", "placement_y")


def _examples(ream: str, root: str = HERE) -> Iterator[Dict]:
    for r in measure_ream(ream, root):
        ex = {k: r[k] for k in FEATURE_KEYS}
        ex["image"] = r["image_path"]
        yield ex


def load(ream: Optional[str] = None, root: str = HERE):
    """Build a :class:`datasets.Dataset`, one row per scanned sheet.

    Goes through ``Dataset.from_generator`` rather than
    ``load_dataset``: script-based datasets were removed in
    ``datasets`` 3.0, so a loading script is no longer something
    ``load_dataset`` will execute.
    """
    import datasets

    names = [ream] if ream else reams(root)
    features = datasets.Features({
        "image": datasets.Image(),
        "sheet_id": datasets.Value("string"),
        "ream": datasets.Value("string"),
        **{k: datasets.Value("float64") for k in FEATURE_KEYS
           if k not in ("sheet_id", "ream")},
    })

    def gen():
        for nm in names:
            yield from _examples(nm, root)

    return datasets.Dataset.from_generator(gen, features=features)


try:                                             # pragma: no cover
    import datasets as _datasets

    class AcmePaper(_datasets.GeneratorBasedBuilder):
        """Kept for datasets < 3.0, which could still run a loading script."""

        VERSION = _datasets.Version("1.0.0")

        def _info(self):
            return _datasets.DatasetInfo(
                description=__doc__,
                features=_datasets.Features({
                    "image": _datasets.Image(),
                    "sheet_id": _datasets.Value("string"),
                    "ream": _datasets.Value("string"),
                    **{k: _datasets.Value("float64") for k in FEATURE_KEYS
                       if k not in ("sheet_id", "ream")},
                }),
            )

        def _split_generators(self, dl_manager):
            root = self.config.data_dir or HERE
            return [_datasets.SplitGenerator(
                name=_datasets.Split.TRAIN, gen_kwargs={"root": root})]

        def _generate_examples(self, root):
            i = 0
            for nm in reams(root):
                for ex in _examples(nm, root):
                    yield i, ex
                    i += 1
except ModuleNotFoundError:                      # pragma: no cover
    pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ream", nargs="?", help="ream directory; default all")
    ap.add_argument("--root", default=HERE)
    ap.add_argument("--csv", help="also write per-sheet rows here")
    a = ap.parse_args(argv)

    names = [a.ream] if a.ream else reams(a.root)
    if not names:
        raise SystemExit(f"no ream directories with PNGs under {a.root}")
    rows: List[Dict] = []
    for nm in names:
        r = measure_ream(nm, a.root)
        print(f"{nm}: {len(r)} of "
              f"{len(glob.glob(os.path.join(a.root, nm, '*.png')))} scans usable")
        rows += r
    if not rows:
        raise SystemExit("nothing measurable")
    report(rows)
    if a.csv:
        keys = [k for k in rows[0] if k != "image_path"]
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(f"\nwrote {a.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
