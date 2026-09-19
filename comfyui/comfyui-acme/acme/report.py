"""Turning poses into something an operator can act on."""

from __future__ import annotations

from typing import Dict, Sequence

import numpy as np

from .fit import Pose


def frame_report(pose: Pose, index: int = 0) -> str:
    lines = [f"frame {index}: {pose.summary()}"]
    if pose.accepted and pose.per_landmark_px:
        worst = max(pose.per_landmark_px.items(), key=lambda kv: kv[1])
        lines.append("    per-landmark px: " + "  ".join(
            f"{k}={v:.2f}" for k, v in pose.per_landmark_px.items()))
        lines.append(f"    worst landmark: {worst[0]} at {worst[1]:.2f} px")
    return "\n".join(lines)


def batch_report(poses: Sequence[Pose]) -> str:
    """A whole batch, with the accept rate and the reasons for the rest.

    A uniformly poor fit and one dog-eared corner are different problems
    and only the per-landmark spread tells them apart, so the worst
    landmark is named rather than averaged away.
    """
    accepted = [p for p in poses if p.accepted]
    lines = [f"{len(accepted)}/{len(poses)} frames registered"]

    if accepted:
        res = np.array([p.peg_residual_px for p in accepted])
        off = np.array([p.punch_offset_mm for p in accepted])
        lines += [
            "",
            f"  residual px   mean {res.mean():.2f}   "
            f"median {np.median(res):.2f}   max {res.max():.2f}",
            f"  punch offset  mean {off.mean()*1000:.0f} um   "
            f"max {off.max()*1000:.0f} um",
            "",
            "  The punch offset is not an error: it is the real "
            "disagreement between",
            "  the sheet outline and the pegs, and it should match the "
            "bench measurement",
            "  in docs/measuring-punch-tolerance.md.  A value far outside "
            "that range",
            "  means the outline or the pegs are being mis-detected.",
        ]
        worst: Dict[str, float] = {}
        for pose in accepted:
            for name, value in pose.per_landmark_px.items():
                worst[name] = max(worst.get(name, 0.0), value)
        lines.append("")
        lines.append("  worst residual seen at each landmark:")
        for name, value in sorted(worst.items(), key=lambda kv: -kv[1]):
            lines.append(f"      {name:<12} {value:.2f} px")

    rejected = [(i, p) for i, p in enumerate(poses) if not p.accepted]
    if rejected:
        lines += ["", f"  {len(rejected)} refused:"]
        for i, pose in rejected:
            lines.append(f"      frame {i}: {pose.reason}")
    return "\n".join(lines)
