"""Write the v4k_01 calibration file from the measured values."""

# SPDX-License-Identifier: GPL-3.0-or-later
# Code, not data: the surrounding directory is CC-BY-SA-4.0.
import glob, json, sys
import numpy as np, cv2
sys.path.insert(0, "/data/piggy/src/github.com/piggyatbaqaqi/storymator/comfyui/comfyui_acme")
from acme.model import Calibration, PegModel, SheetModel, FieldSpec

D = "/data/piggy/src/github.com/piggyatbaqaqi/storymator/data/calibration/distortion/v4k_01/"
SQ, ANISO = 25.3163, 0.0015          # measured square; measured print anisotropy
adict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
board = cv2.aruco.CharucoBoard((7, 9), SQ, SQ*18/25, adict)
det = cv2.aruco.CharucoDetector(board)
objp = board.getChessboardCorners()

img, objs, size = [], [], None
for f in sorted(glob.glob(D + "distortion-*.jpg")):
    g = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    if g is None: continue
    size = g.shape[::-1]
    cc, ci, _, _ = det.detectBoard(g)
    if cc is None or len(cc) < 12: continue
    o = objp[ci.ravel()].copy()
    o[:, 0] *= (1 + ANISO/2); o[:, 1] *= (1 - ANISO/2)
    objs.append(o.astype(np.float32)); img.append(cc.reshape(-1,2).astype(np.float32))

rms, K, dist, _, _ = cv2.calibrateCamera(objs, img, size, None, None)
print(f"{len(img)} frames, {sum(len(p) for p in img)} corners, rms {rms:.4f}")
print(f"fx {K[0,0]:.2f}  fy {K[1,1]:.2f}  cx {K[0,2]:.1f}  cy {K[1,2]:.1f}")
print("dist", np.round(dist.ravel(), 6).tolist())

cal = Calibration(
    peg=PegModel(round_diameter_mm=6.440,     # slip test, +/-0.010
                 rect_long_mm=12.72,          # left 12.700, right 12.740
                 rect_short_mm=3.142,         # 6 readings, sd 0.092
                 centre_spacing_mm=101.616),  # 94 sheets, sd 0.026
    sheet=SheetModel(), field_spec=FieldSpec(),
    camera_matrix=K, dist_coeffs=dist.ravel())
d = cal.to_dict()
d["_provenance"] = {
    "camera": "v4k_01", "bar": "honbay_0001", "target": "charuco_0001",
    "usb_id": "1778:d009", "usb_product": "IPEVO V4K",
    "usb_serial": None,
    "frame_size_px": list(size),
    "focus_absolute": 134,
    "required_controls": {"white_balance_automatic": 0, "auto_exposure": 1,
                          "focus_automatic_continuous": 0, "focus_absolute": 134},
    "board_square_mm": SQ, "board_anisotropy": ANISO,
    "calibrated": "2026-09-18", "frames": len(img), "rms_px": round(float(rms), 4),
    "notes": "Valid ONLY at focus_absolute 134. The V4K reports no USB "
             "serial, so identity cannot be checked; verify the controls "
             "and frame size instead.",
}
out = D + "v4k_01.json"
open(out, "w").write(json.dumps(d, indent=2))
print("wrote", out)
