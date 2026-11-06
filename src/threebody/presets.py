"""Starting setups worth looking at, with the sources of their numbers."""

from __future__ import annotations

import math

from threebody.config import SetupConfig

# Chenciner & Montgomery (2000): three equal masses chasing each other along one figure-eight.
# Initial conditions as given by Simó; the period is about 6.3259.
FIGURE_EIGHT = SetupConfig(
    masses=(1.0, 1.0, 1.0),
    positions=((-0.97000436, 0.24308753), (0.97000436, -0.24308753), (0.0, 0.0)),
    velocities=((0.46620368, 0.43236573), (0.46620368, 0.43236573), (-0.93240737, -0.86473146)),
    duration=6.3259,
)
FIGURE_EIGHT_PERIOD = 6.32591398

# Lagrange (1772): equal masses on an equilateral triangle, rotating rigidly. For three masses m at
# distance r from the centre, circular motion needs speed sqrt(G m / (sqrt(3) r)).
_v = math.sqrt(1.0 / math.sqrt(3.0))
LAGRANGE_TRIANGLE = SetupConfig(
    masses=(1.0, 1.0, 1.0),
    positions=tuple(
        (math.cos(a), math.sin(a))
        for a in (math.pi / 2, math.pi / 2 + 2 * math.pi / 3, math.pi / 2 + 4 * math.pi / 3)
    ),  # type: ignore[arg-type]
    velocities=tuple(
        (-_v * math.sin(a), _v * math.cos(a))
        for a in (math.pi / 2, math.pi / 2 + 2 * math.pi / 3, math.pi / 2 + 4 * math.pi / 3)
    ),  # type: ignore[arg-type]
    duration=12.0,
)

# Burrau's "Pythagorean" problem (1913): masses 3, 4 and 5 at rest on the corners of a 3-4-5
# triangle. Chaotic close encounters, until one body is thrown out.
PYTHAGOREAN = SetupConfig(
    masses=(3.0, 4.0, 5.0),
    positions=((1.0, 3.0), (-2.0, -1.0), (1.0, -1.0)),
    velocities=((0.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
    duration=20.0,
)

PRESETS: dict[str, SetupConfig] = {
    "Figure-eight": FIGURE_EIGHT,
    "Lagrange triangle": LAGRANGE_TRIANGLE,
    "Pythagorean (chaotic)": PYTHAGOREAN,
}
