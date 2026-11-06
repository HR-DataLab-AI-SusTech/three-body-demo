"""A setup: what a visitor can choose, with the bounds that keep a public form harmless."""

from __future__ import annotations

from typing import Annotated

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from threebody.physics import Trajectory, simulate

Mass = Annotated[float, Field(ge=0.01, le=100.0)]
Coordinate = Annotated[float, Field(ge=-10.0, le=10.0)]
Speed = Annotated[float, Field(ge=-10.0, le=10.0)]
Vector = tuple[Coordinate, Coordinate]
Velocity = tuple[Speed, Speed]


class SetupConfig(BaseModel):
    """Three masses, where they start and how fast they move, and how long to watch."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    masses: tuple[Mass, Mass, Mass]
    positions: tuple[Vector, Vector, Vector]
    velocities: tuple[Velocity, Velocity, Velocity]
    duration: Annotated[float, Field(ge=1.0, le=100.0)] = 10.0

    def run(self, frames: int | None = None) -> Trajectory:
        # About 15 frames per time unit, so a long orbit is not drawn in a few big jumps.
        n = frames or int(min(1500, max(300, 15 * self.duration)))
        return simulate(
            np.array(self.masses),
            np.array(self.positions),
            np.array(self.velocities),
            duration=self.duration,
            frames=n,
        )
