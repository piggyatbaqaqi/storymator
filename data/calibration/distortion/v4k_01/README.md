# Camera v4k_01
## Model
* IPEVO V4K UHD USB Document Camera
* https://www.bhphotovideo.com/c/product/1694948-REG/ipevo_v4k_ultra_high_definition.html
## Settings
* white_balance_automatic = 0 (off)
* auto_exposure = 1 (Manual Mode)
* focus_automatic_continuous = 0 (off)
* focus_absolute = 134

# ACME peg bar honbay_0001
## Model
* Honbay Comic Tool Stainless Steel Ruler Fixed Paper Feet for Fixing Animation Position Paper
* https://www.amazon.com/dp/B0721MR5TM?ref=ppx_yo2ov_dt_b_fed_asin_title
## Mounting
* 3M Command X-Large Picture Hanging Strips 20lb
* barcode: 68060 46365
## Location
* Monte's office desk, Ashland Haus

# Target charuco_0001
## File
* ../../targets/calibrx-charuco-175x225mm.svg

# Files
* abused_sheet-1.raw - Reference sheet that just lives on the desk. It's bent and water damaged.
* anisotropy_scan.py - Refits the whole distortion-*.raw set with the
  board's x and y scaled independently, to ask whether charuco_0001's
  print is anisotropic. Sweeps the anisotropy and reports rms, fx and fy
  for each value; minimum rms and fx=fy both land at +0.15 %, and a
  reversed control is much worse, which is what makes it a measurement
  rather than a free parameter soaking up noise. Needs no arguments --
  the board parameters are constants at the top.
* camera_settings.gpfl - These are the camera settings used to calibrate v4k_01.
* check_mount-*.raw - These images confirm the flatness of charuco_0001.
* distortion-*.raw - Shots of the calbration target charuco_0001 to calibrate v4k_01.
* fresh_sheet-1.raw - A new blank sheet for comparison with abused_sheet-1.raw.
* bar_reference.raw - *(was `glass_reference.raw`.)* You are right that
  it is not the glass reference, and I have no memory that contradicts
  you: the glass shot was numbered into the distortion set during the
  first session and overwritten when the set was re-shot on the foam
  board. It is lost.
  What this actually is: **the only in-situ photograph of honbay_0001**,
  showing the bar on the desk with all three pegs, shot at 16:07.
  charuco_0001 is in frame too, as loose paper before the foam-board
  mount -- which incidentally makes it the surviving evidence for the
  loose-paper mounting that gave 5.25 px homography residuals, cited in
  `docs/calibrating-a-camera.md` as the largest single error source of
  the exercise. Renamed rather than removed on the first ground.
* peg_profile-*.raw - Profile pictures of honbay_0001's round peg, to
  get the effective height that drives the peg-top parallax correction.
  1-4 are at ~190 mm and out of focus, because the camera moved in while
  `focus_absolute` stayed at 134 (focus for 380 mm). **peg_profile-5.raw
  is the usable one: 57 mm, `focus_absolute 635`**, edge 10-90 rise
  11 px. It establishes that the dome is hemispherical (b/a = 0.980) and
  so that h_eff = 5.567 mm. Note the non-default focus: these frames are
  deliberately outside the v4k_01 calibration, which is valid only at
  focus 134. That is sound here because the measurement is a *ratio* and
  needs no intrinsics.
  Analysis and results: `../../pegs/honbay_0001/README.md`.
