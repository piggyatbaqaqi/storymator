"""Absolute hole size, sub-pixel, three independent ways."""
import glob, os
import numpy as np
from PIL import Image
from scipy import ndimage

DPI = 300.0; MM = 25.4 / DPI
D = "data/calibration/paper/"

def holes(path):
    a = np.asarray(Image.open(path).convert("L"), float)
    sheet = a > 128
    lab, n = ndimage.label(sheet)
    if n == 0: return None
    sizes = ndimage.sum(sheet, lab, range(1, n + 1))
    sheet = lab == int(np.argmax(sizes)) + 1
    h = ndimage.binary_fill_holes(sheet) & ~sheet
    lab2, n2 = ndimage.label(h)
    out = []
    for i, box in enumerate(ndimage.find_objects(lab2), start=1):
        if box is None: continue
        m = lab2[box] == i
        if not (2000 < m.sum() < 20000): continue
        yy, xx = np.nonzero(m)
        c = np.array([xx.mean() + box[1].start, yy.mean() + box[0].start])
        ext = np.ptp(np.column_stack([xx, yy]), axis=0)
        out.append((c, float(min(ext)), float(max(ext)), m.sum()))
    if len(out) != 3: return None
    out.sort(key=lambda t: t[0][1])
    return a, out

def ray_diameter(a, c, black, white, rmax=60, n=720):
    """50 % crossing of the edge profile along n rays from the centre."""
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = np.arange(0, rmax, 0.25)
    xs = c[0] + np.outer(np.cos(th), r)
    ys = c[1] + np.outer(np.sin(th), r)
    v = ndimage.map_coordinates(a, [ys.ravel(), xs.ravel()], order=1)
    v = v.reshape(n, len(r))
    half = (black + white) / 2.0
    radii = []
    for row in v:
        k = np.argmax(row > half)
        if k == 0: continue
        lo, hi = row[k - 1], row[k]
        if hi <= lo: continue
        radii.append(r[k - 1] + (half - lo) / (hi - lo) * 0.25)
    return 2 * np.median(radii) if radii else np.nan

files = sorted(glob.glob(D + "*.png"))[:40]
rows = []
for f in files:
    g = holes(f)
    if not g: continue
    a, hs = g
    (c, s, l, area) = hs[1]                      # middle = round hole
    if l / max(s, 1e-9) > 1.4: continue
    win = a[int(c[1]) - 70:int(c[1]) + 70, int(c[0]) - 70:int(c[0]) + 70]
    if win.size == 0: continue
    black = np.percentile(win, 2); white = np.percentile(win, 98)
    rows.append(dict(
        ptp=(s + l) / 2 * MM,                    # what the old script did
        ptp1=((s + 1) + (l + 1)) / 2 * MM,       # + the off-by-one
        area=2 * np.sqrt(area / np.pi) * MM,     # hard-threshold area
        ray=ray_diameter(a, c, black, white) * MM,
        rect_s=(hs[0][1] + hs[2][1]) / 2 * MM,
        rect_s1=(hs[0][1] + 1 + hs[2][1] + 1) / 2 * MM,
    ))

def rep(k, nominal=None):
    v = np.array([r[k] for r in rows]); v = v[np.isfinite(v)]
    s = f"  {k:8s} {v.mean():7.4f} mm   sd {v.std(ddof=1):.4f}   n={len(v)}"
    if nominal: s += f"   vs peg {nominal:.3f} -> {v.mean()-nominal:+.4f}"
    print(s)

print("ROUND HOLE (round peg = 6.350 mm)")
for k in ("ptp", "ptp1", "area", "ray"): rep(k, 6.350)
print("\nRECT HOLE, SHORT AXIS (rect peg short = 3.175 mm)")
for k in ("rect_s", "rect_s1"): rep(k, 3.175)
