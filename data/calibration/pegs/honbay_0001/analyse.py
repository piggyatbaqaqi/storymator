# SPDX-License-Identifier: GPL-3.0-or-later
# Code, not data: the surrounding directory is CC-BY-SA-4.0.

import numpy as np
def s(name, vals, nominal=None, note=""):
    v = np.array(vals, float); m = v.mean()
    sd = v.std(ddof=1); se = sd/np.sqrt(len(v))
    out = f"{name:34s} {m:7.3f}  sd {sd:5.3f}  se {se:5.3f}  n={len(v)}"
    if nominal is not None:
        out += f"   nom {nominal:6.3f} -> {m-nominal:+.3f} ({(m-nominal)/0.0254:+.1f} thou)"
    print(out + ("  " + note if note else ""))
    return m, sd, se

IN = 25.4
print("=== PEGS ===")
rd,_,_   = s("round peg diameter",        [6.49,6.49,6.45], IN/4)
rl,_,_   = s("rect peg length, left",     [12.71,12.70,12.69], IN/2)
rr,_,_   = s("rect peg length, right",    [12.74,12.75,12.73], IN/2)
tl,_,sel = s("rect peg thickness, left",  [3.30,3.17,3.12], IN/8)
tr,_,ser = s("rect peg thickness, right", [3.11,3.02,3.13], IN/8)
s("rect peg thickness, both",             [3.30,3.17,3.12,3.11,3.02,3.13], IN/8)

print("\n=== HEIGHTS (the parallax lever arms) ===")
hr,_,_ = s("round peg above paper",  [8.92,8.61,8.83])
hrb,_,_= s("round peg above bar",    [9.04,9.32,8.76])
hl,_,_ = s("rect peg above paper, L",[6.24,6.40,6.26])
hrr,_,_= s("rect peg above paper, R",[6.35,5.99,6.32])
hx,_,_ = s("rect peg above paper, both",[6.24,6.40,6.26,6.35,5.99,6.32])
hb,_,_ = s("bar above desk",         [4.32,5.21,5.00], note="<- the wavy one")
hp,_,_ = s("paper above desk",       [0.49,0.70,0.37,0.66])

print("\n=== CALIPER ZERO CHECK ===")
print(f"  left rect peg length reads {rl:.3f} against a 12.700 nominal, sd 0.010.")
print(f"  A zero offset big enough to explain the round peg would put it at "
      f"{12.700+(rd-IN/4):.3f}.  There is no zero offset.")

print("\n=== ROUND PEG vs MY OPTICAL HOLE ===")
for nm, d in (("50% edge crossing", 6.3105), ("thresholded area", 6.2925),
              ("extent + 1 px", 6.3478)):
    print(f"  hole {nm:20s} {d:.4f}   peg - hole = {rd-d:+.4f} mm")
print("  All negative.  The sheet mounts, so the optical hole reads small")
print(f"  by at least {rd-6.3478:.2f} mm, i.e. {(rd-6.3478)/(25.4/300):.1f} px at 300 dpi.")

print("\n=== PARALLAX: apparent outward shift of a peg top ===")
print("  delta = r * h / (Z - h)        r = lateral offset from the optical axis")
print(f"\n  {'Z (mm)':>8} | {'round peg, r=20':>16} | {'rect pegs, r=101.6':>19} | "
      f"{'apparent span':>14} | {'rigid-fit rms':>13}")
print("  " + "-"*80)
for Z in (300, 380, 450):
    dr = 20*hr/(Z-hr)
    dx = 101.6*hx/(Z-hx)
    span = 203.2 + 2*dx
    rms = np.sqrt((0 + dx**2 + dx**2)/3)
    print(f"  {Z:8.0f} | {dr:13.2f} mm | {dx:16.2f} mm | {span:11.2f} mm | {rms:10.2f} mm")
print(f"\n  Observed peg residual was 1.6-2.3 mm.  Nominal span 203.2 mm.")

print("\n=== SOLVING h_eff FROM AN OBSERVED SPAN ===")
print("  apparent = 203.2 * Z/(Z-h)   ->   h = Z * (1 - 203.2/apparent)")
for Z in (380,):
    for ap in (204.0, 205.0, 206.0, 207.0):
        print(f"    Z={Z}  apparent span {ap:.1f} mm  ->  h_eff = {Z*(1-203.2/ap):5.2f} mm")
print(f"  (full rect peg height is {hx:.2f} mm; the detector sees top face + flank,")
print("   so h_eff should land between h/2 and h)")

print("\n=== THE SHEET IS NOT FLAT ===")
print(f"  bar above desk   {hb:.2f} mm")
print(f"  paper above desk {hp:.2f} mm")
print(f"  so the punched edge is lifted {hb-hp:.2f} mm above the rest of the sheet.")
for ang in (10, 20, 30):
    print(f"    at {ang} deg obliquity that is "
          f"{(hb-hp)*np.tan(np.radians(ang)):.2f} mm of lateral error near the bar")

print("\n=== PAPER THICKNESS: two routes disagree ===")
print(f"  round peg (above bar - above paper) = {hrb-hr:.3f} mm")
print(f"  paper above desk                    = {hp:.3f} mm")
print("  bond is ~0.10 mm.  Neither route measures it well.")
