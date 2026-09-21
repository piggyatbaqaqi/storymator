import glob
import numpy as np, cv2
D = "data/calibration/distortion/v4k_01/"
COLS, ROWS, SQ = 7, 9, 25.3163
adict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
board = cv2.aruco.CharucoBoard((COLS, ROWS), SQ, SQ*18/25, adict)
det = cv2.aruco.CharucoDetector(board)
objp = board.getChessboardCorners()
img_pts, ids_all, size = [], [], None
for f in sorted(glob.glob(D + "distortion-*.jpg")):
    g = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    if g is None: continue
    size = g.shape[::-1]
    cc, ci, _, _ = det.detectBoard(g)
    if cc is None or len(cc) < 12: continue
    img_pts.append(cc.reshape(-1,2).astype(np.float32)); ids_all.append(ci.ravel())

def run(a):                      # a = fractional anisotropy, x stretched by a/2, y by -a/2
    objs = []
    for ids in ids_all:
        o = objp[ids].copy(); o[:,0] *= (1+a/2); o[:,1] *= (1-a/2)
        objs.append(o.astype(np.float32))
    rms, K, *_ = cv2.calibrateCamera(objs, img_pts, size, None, None)
    return rms, K[0,0], K[1,1]

print(f"  {'anisotropy':>11} | {'rms':>7} | {'fx':>8} | {'fy':>8} | {'fx/fy - 1':>10}")
print("  " + "-"*56)
best = None
for a in (-0.0038, 0.0, 0.0010, 0.0015, 0.0020, 0.0025, 0.0038):
    rms, fx, fy = run(a)
    mark = ""
    if best is None or rms < best[1]: best = (a, rms); mark = "  <-- best so far"
    print(f"  {100*a:+10.3f} % | {rms:7.4f} | {fx:8.2f} | {fy:8.2f} | {100*(fx/fy-1):+9.3f} %{mark}")
print(f"\n  calipers said +0.38 %, sd 0.26 %.  The data says about +0.15 %.")
