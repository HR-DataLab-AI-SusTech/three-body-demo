"""Setups worth watching, with where their numbers come from.

Every periodic one carries its period, and tests/test_physics.py checks that it closes in this
app's own integrator after one period; an orbit that did not close would not be here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from threebody.config import SetupConfig


@dataclass(frozen=True)
class Preset:
    config: SetupConfig
    description: str
    period: float | None = None  # set for a periodic orbit: it returns to its start after this


def _sd2013(p1: float, p2: float, period: float, periods: float = 2.0) -> SetupConfig:
    """Šuvakov & Dmitrašinović's setup: equal masses at (-1, 0), (1, 0), (0, 0), the outer two with
    velocity (p1, p2) and the middle one with (-2 p1, -2 p2), so the centre of mass stands still."""
    return SetupConfig(
        masses=(1.0, 1.0, 1.0),
        positions=((-1.0, 0.0), (1.0, 0.0), (0.0, 0.0)),
        velocities=((p1, p2), (p1, p2), (-2 * p1, -2 * p2)),
        duration=min(round(period * periods, 2), 100.0),
    )


SD2013 = "Šuvakov & Dmitrašinović, Phys. Rev. Lett. 110, 114301 (2013)"

# Chenciner & Montgomery (2000): three equal masses chasing each other along one figure-eight;
# initial conditions as given by Simó.
FIGURE_EIGHT_PERIOD = 6.32591398
FIGURE_EIGHT = SetupConfig(
    masses=(1.0, 1.0, 1.0),
    positions=((-0.97000436, 0.24308753), (0.97000436, -0.24308753), (0.0, 0.0)),
    velocities=((0.46620368, 0.43236573), (0.46620368, 0.43236573), (-0.93240737, -0.86473146)),
    duration=12.65,
)

# Lagrange (1772): equal masses on an equilateral triangle, rotating rigidly. Three masses m at
# distance r from the centre move in circles at speed sqrt(G m / (sqrt(3) r)).
_v = math.sqrt(1.0 / math.sqrt(3.0))
_angles = (math.pi / 2, math.pi / 2 + 2 * math.pi / 3, math.pi / 2 + 4 * math.pi / 3)
LAGRANGE_TRIANGLE = SetupConfig(
    masses=(1.0, 1.0, 1.0),
    positions=tuple((math.cos(a), math.sin(a)) for a in _angles),  # type: ignore[arg-type]
    velocities=tuple((-_v * math.sin(a), _v * math.cos(a)) for a in _angles),  # type: ignore[arg-type]
    duration=12.0,
)

# Burrau's "Pythagorean" problem (1913): masses 3, 4 and 5 at rest on the corners of a 3-4-5
# triangle. Chaotic close encounters, until one body is thrown out (around t = 60).
PYTHAGOREAN = SetupConfig(
    masses=(3.0, 4.0, 5.0),
    positions=((1.0, 3.0), (-2.0, -1.0), (1.0, -1.0)),
    velocities=((0.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
    duration=70.0,
)

PRESETS: dict[str, Preset] = {
    "Figure-eight": Preset(
        FIGURE_EIGHT,
        "Three equal masses chasing each other along one figure-eight "
        "(Chenciner & Montgomery 2000). Two laps.",
        FIGURE_EIGHT_PERIOD,
    ),
    "Lagrange triangle": Preset(
        LAGRANGE_TRIANGLE,
        "An equilateral triangle that turns without changing shape (Lagrange 1772). Unstable: "
        "nudge one body and watch it fall apart.",
    ),
    "Pythagorean (chaotic)": Preset(
        PYTHAGOREAN,
        "Masses 3, 4 and 5 at rest on a 3-4-5 triangle (Burrau 1913): close encounters, until one "
        "body is flung out for good.",
    ),
    "Butterfly I": Preset(_sd2013(0.306893, 0.125507, 6.2356), f"Two wings. {SD2013}.", 6.2356),
    "Butterfly II": Preset(_sd2013(0.392955, 0.097579, 7.0039), f"{SD2013}.", 7.0039),
    "Butterfly III": Preset(_sd2013(0.405916, 0.230163, 13.8658), f"{SD2013}.", 13.8658),
    "Butterfly IV": Preset(
        _sd2013(0.350112, 0.079339, 79.4759, periods=1),
        f"The long one: about 79 time units before it repeats. {SD2013}.",
        79.4759,
    ),
    "Moth I": Preset(_sd2013(0.464445, 0.396060, 14.8939), f"{SD2013}.", 14.8939),
    "Moth II": Preset(_sd2013(0.439166, 0.452968, 28.6703), f"{SD2013}.", 28.6703),
    "Moth III": Preset(_sd2013(0.383444, 0.377364, 25.8406), f"{SD2013}.", 25.8406),
    "Bumblebee": Preset(
        _sd2013(0.184279, 0.587188, 63.5345, periods=1),
        f"A long, busy orbit: about 64 time units per lap. {SD2013}.",
        63.5345,
    ),
    "Goggles": Preset(_sd2013(0.083300, 0.127889, 10.4668), f"{SD2013}.", 10.4668),
    "Dragonfly": Preset(_sd2013(0.080584, 0.588836, 21.2710), f"{SD2013}.", 21.2710),
    "Yarn": Preset(
        _sd2013(0.559064, 0.349192, 55.5018, periods=1),
        f"Winds itself into a ball of yarn. {SD2013}.",
        55.5018,
    ),
    "Yin-yang Ia": Preset(_sd2013(0.513938, 0.304736, 17.3284), f"{SD2013}.", 17.3284),
    "Yin-yang Ib": Preset(_sd2013(0.282699, 0.327209, 10.9626), f"{SD2013}.", 10.9626),
}
