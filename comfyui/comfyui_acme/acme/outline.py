"""Two candidate replacements for the sheet's corner finder.

:func:`acme.detect.sheet_corners` sorts boundary points into four
sides using a local frame from :func:`acme.detect._principal_angle`,
which takes the sheet's orientation from the **second moments of its
area**.  On this rig that is degenerate, not merely inaccurate.

A 279.4 x 215.9 mm sheet has an aspect ratio of 1.29, but seen from
the camera's angle the long axis foreshortens and the mask comes out
essentially square: measured over the whole corpus, **43 of 46 frames
sit between 1.00 and 1.06**.  The covariance of a square is isotropic,
so its principal axis is arbitrary -- and the reported angle duly
wanders between 1 and 45 degrees with no relation to how the sheet is
actually placed.  Squaring the bar to the frame does not help, and the
`square` session was shot to check exactly that: the sheet is visibly
square in `square_013` and `square_014`, and the angle comes back
-31.5 and -44.4 degrees.

The frames it gets right are the ones where the arbitrary axis happens
to land near zero.  That is luck, and it has been carrying the whole
outline stage.

Both candidates below take the orientation from the **boundary**
instead, where the corners are.  They are kept side by side so the
choice is made by measurement rather than by argument; `outline_test`
runs the same battery against each.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np


def _cv2():
    import cv2
    return cv2


def corners_min_area_rect(mask: np.ndarray,
                          gray: Optional[np.ndarray] = None,
                          return_samples: bool = False):
    """Orientation from ``cv2.minAreaRect``, then the existing side sort.

    The smallest enclosing rotated rectangle is fixed by the extreme
    points of the boundary, so a near-square mask is no obstacle: a
    square has a well-defined minimum-area box even though it has no
    well-defined principal axis.

    The smaller change of the two.  Everything after the local frame --
    the four-way sort, the middle-80 % trim, the sub-pixel gradient
    refinement, the intersection of fitted lines -- is kept, so the
    sub-pixel accuracy that the rigid peg stage depends on is kept
    with it.

    It inherits one weakness: the box is fitted to the *convex hull*,
    and a keystoned quadrilateral is not a rotated rectangle, so the
    box's angle is a compromise between the two pairs of opposite
    edges rather than either one.
    """
    raise NotImplementedError


def corners_approx_poly(mask: np.ndarray,
                        gray: Optional[np.ndarray] = None,
                        return_samples: bool = False):
    """The quadrilateral itself, from ``cv2.approxPolyDP``.

    No local frame and no four-way sort: Douglas-Peucker reduces the
    contour to its four dominant vertices directly, and boundary points
    are assigned to a side by which pair of vertices they fall between.
    A keystone is not a special case, because nothing here assumes the
    shape is a rectangle.

    This is the method the paper-bow measurement in
    docs/planning/ink-landmarks.md already uses successfully on these
    very frames, `fresh_ink_007` included.

    The larger change, and it has to earn it: ``approxPolyDP`` returns
    whatever vertex count its tolerance produces, so a rounded or
    dog-eared corner can give three or five, and the epsilon that
    yields four is not knowable in advance.  The implementation is
    expected to search for it rather than take a fixed fraction of the
    perimeter.
    """
    raise NotImplementedError


def corner_order(corners: np.ndarray) -> np.ndarray:
    """Corners in a consistent, non-mirrored cyclic order.

    Winding matters downstream: :func:`acme.fit.fit_pose` rejects a
    homography whose linear part has a negative determinant, on the
    grounds that it describes a sheet seen from behind.  A corner
    finder that returns its vertices in whichever order the contour
    tracer happened to walk would make that check fire at random.
    """
    raise NotImplementedError


def outline_quality(corners: np.ndarray, mask: np.ndarray) -> Tuple[float,
                                                                    float]:
    """``(iou, worst_corner_distance_px)`` of a quad against the mask.

    The measure the two candidates are compared on. IoU alone hides a
    single bad corner in a large area; the worst corner alone ignores a
    quad that is wrong everywhere by a little.
    """
    raise NotImplementedError
