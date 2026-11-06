"""Three bodies under Newtonian gravity in a plane, integrated with velocity Verlet.

Units are chosen so that G = 1. Velocity Verlet is symplectic: it does not conserve energy exactly,
but its error stays bounded instead of growing, which is why a figure-eight orbit still closes after
many periods. A small softening length keeps a near-collision from producing an infinite force.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

G = 1.0

Array = NDArray[np.float64]


@dataclass(frozen=True)
class Trajectory:
    """Positions at each recorded step, shape (frames, 3, 2), with their times and energies."""

    times: Array
    positions: Array
    energies: Array

    @property
    def energy_drift(self) -> float:
        """Largest relative departure of the total energy from its starting value."""
        e0 = self.energies[0]
        return float(np.max(np.abs(self.energies - e0)) / max(abs(e0), 1e-12))


def accelerations(positions: Array, masses: Array, softening: float) -> Array:
    """The acceleration of each body from the other two, shape (3, 2)."""
    diff = positions[None, :, :] - positions[:, None, :]  # r_j - r_i, shape (3, 3, 2)
    dist2 = np.sum(diff**2, axis=-1) + softening**2
    np.fill_diagonal(dist2, np.inf)  # a body does not pull on itself
    inv_r3 = dist2**-1.5
    return G * np.sum(diff * (masses[None, :, None] * inv_r3[:, :, None]), axis=1)


def energy(positions: Array, velocities: Array, masses: Array, softening: float) -> float:
    """Kinetic plus potential energy of the system."""
    kinetic = 0.5 * float(np.sum(masses * np.sum(velocities**2, axis=-1)))
    potential = 0.0
    for i in range(3):
        for j in range(i + 1, 3):
            r = np.sqrt(np.sum((positions[i] - positions[j]) ** 2) + softening**2)
            potential -= G * masses[i] * masses[j] / r
    return kinetic + potential


def simulate(
    masses: Array,
    positions: Array,
    velocities: Array,
    *,
    duration: float,
    dt: float = 1e-3,
    frames: int = 300,
    softening: float = 1e-3,
) -> Trajectory:
    """Integrate for `duration` time units in steps of `dt`, keeping about `frames` snapshots."""
    if duration <= 0 or dt <= 0:
        raise ValueError("duration and dt must be positive")
    m = np.asarray(masses, dtype=np.float64)
    x = np.asarray(positions, dtype=np.float64).copy()
    v = np.asarray(velocities, dtype=np.float64).copy()
    if m.shape != (3,) or x.shape != (3, 2) or v.shape != (3, 2):
        raise ValueError("expected 3 masses and 3 two-dimensional positions and velocities")

    steps = round(duration / dt)
    every = max(1, steps // frames)
    times, snaps, energies = [0.0], [x.copy()], [energy(x, v, m, softening)]

    a = accelerations(x, m, softening)
    for step in range(1, steps + 1):
        v += 0.5 * dt * a
        x += dt * v
        a = accelerations(x, m, softening)
        v += 0.5 * dt * a
        if step % every == 0 or step == steps:
            times.append(step * dt)
            snaps.append(x.copy())
            energies.append(energy(x, v, m, softening))

    return Trajectory(np.array(times), np.array(snaps), np.array(energies))


def centre_of_mass_frame(masses: Array, positions: Array, velocities: Array) -> tuple[Array, Array]:
    """Shift positions and velocities so the centre of mass sits still at the origin."""
    m = np.asarray(masses, dtype=np.float64)
    x = np.asarray(positions, dtype=np.float64)
    v = np.asarray(velocities, dtype=np.float64)
    total = m.sum()
    return x - (m @ x) / total, v - (m @ v) / total
