"""Round punch diameter across the whole ream, three ways."""

# SPDX-License-Identifier: GPL-3.0-or-later
# Code, not data: the surrounding directory is CC-BY-4.0.
import glob
import numpy as np
from PIL import Image
from scipy import ndimage

MM = 25.4/300.0
D = "data/calibration/paper/"

def ray_diameter(a, c, black, white, rmax=60, n=720):
    th = np.linspace(0, 2*np.pi, n, endpoint=False)
    r = np.arange(0, rmax, 0.25)
    xs = c[0] + np.outer(np.cos(th), r); ys = c[1] + np.outer(np.sin(th), r)
    v = ndimage.map_coordinates(a, [ys.ravel(), xs.ravel()], order=1).reshape(n, len(r))
    half = (black + white)/2.0
    radii = []
    for row in v:
        k = int(np.argmax(row > half))
        if k == 0: continue
        lo, hi = row[k-1], row[k]
        if hi <= lo: continue
        radii.append(r[k-1] + (half-lo)/(hi-lo)*0.25)
    return 2*np.median(radii) if radii else np.nan

def measure(path):
    a = np.asarray(Image.open(path).convert("L"), float)
    sheet = a > 128
    lab, n = ndimage.label(sheet)
    if n == 0: return None
    sheet = lab == 1+int(np.argmax(ndimage.sum(sheet, lab, range(1, n+1))))
    holes = ndimage.binary_fill_holes(sheet) & ~sheet
    l2, n2 = ndimage.label(holes)
    found = []
    for i, box in enumerate(ndimage.find_objects(l2), 1):
        if box is None: continue
        m = l2[box] == i
        if not (2000 < m.sum() < 20000): continue
        yy, xx = np.nonzero(m)
        c = np.array([xx.mean()+box[1].start, yy.mean()+box[0].start])
        ext = np.ptp(np.column_stack([xx, yy]), axis=0) + 1.0   # +1: ptp is centre-to-centre
        found.append((c, float(min(ext)), float(max(ext)), float(m.sum())))
    if len(found) != 3: return None
    found.sort(key=lambda t: t[0][1])
    c, s_, l_, area = found[1]
    if l_/max(s_, 1e-9) > 1.4: return None
    w = a[int(c[1])-70:int(c[1])+70, int(c[0])-70:int(c[0])+70]
    if w.size == 0: return None
    black, white = np.percentile(w, 2), np.percentile(w, 98)
    return dict(ray=ray_diameter(a, c, black, white)*MM,
                area=2*np.sqrt(area/np.pi)*MM,
                ext=(s_+l_)/2*MM)

rows = [r for r in (measure(f) for f in sorted(glob.glob(D+"*.png"))) if r]
print(f"round punch, {len(rows)} sheets of 95\n")
print(f"  {'method':30s} {'mean':>7} {'sd':>7} {'min':>7} {'max':>7} {'range':>7}")
for k, name in (("ray", "50 % edge crossing, 720 rays"),
                ("area", "thresholded area"),
                ("ext", "extent + 1 px")):
    v = np.array([r[k] for r in rows]); v = v[np.isfinite(v)]
    print(f"  {name:30s} {v.mean():7.3f} {v.std(ddof=1):7.4f} {v.min():7.3f} "
          f"{v.max():7.3f} {np.ptp(v):7.3f}")
v = np.array([r["ray"] for r in rows]); v = v[np.isfinite(v)]
sd = v.std(ddof=1)
print(f"\n  spread on the principled method: sd {sd:.4f} mm = {1000*sd:.0f} um "
      f"= {100*sd/v.mean():.2f} % of the mean")
print(f"  se of the mean: {sd/np.sqrt(len(v)):.4f} mm")
lo, hi = np.percentile(v, [2.5, 97.5])
print(f"  95 % of sheets fall in {lo:.3f} - {hi:.3f} mm (a {hi-lo:.3f} mm band)")
print(f"\n  peg 6.440 +/- 0.010 ; optical mean {v.mean():.3f} -> reads "
      f"{6.440-v.mean():.3f} mm SMALL, as a grip fit requires")
