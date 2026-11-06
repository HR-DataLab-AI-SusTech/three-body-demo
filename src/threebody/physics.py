"""Three bodies under Newtonian gravity in a plane.

Units are chosen so that G = 1. The equations are integrated by DOP853, an adaptive eighth-order
Runge-Kutta method: it takes tiny steps only while two bodies pass close and long ones elsewhere,
which is what lets the published periodic orbits (many with very close passes) close in about a
second. The softening is tiny on purpose: 1e-3 already bends those orbits off course (measured),
while 1e-6 only keeps a head-on collision finite. A ceiling on the work done stops a pathological
setup from occupying the server.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

G = 1.0
# Right-hand-side evaluations allowed for one run (about 8 µs each). The longest preset,
# Butterfly IV, needs about 180 000; a head-on collision passes the softening in about 33 000.
MAX_EVALUATIONS = 600_000

Array = NDArray[np.float64]


class TooCloseError(Exception):
    """The bodies came so close that following them would take too long."""


@dataclass(frozen=True)
class Trajectory:
    """Positions at evenly spaced times, shape (frames, 3, 2), with those times and the energies."""

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
    frames: int = 300,
    softening: float = 1e-6,
    tolerance: float = 1e-10,
) -> Trajectory:
    """Integrate for `duration` time units and sample `frames` evenly spaced snapshots."""
    if duration <= 0:
        raise ValueError("duration must be positive")
    m = np.asarray(masses, dtype=np.float64)
    x0 = np.asarray(positions, dtype=np.float64)
    v0 = np.asarray(velocities, dtype=np.float64)
    if m.shape != (3,) or x0.shape != (3, 2) or v0.shape != (3, 2):
        raise ValueError("expected 3 masses and 3 two-dimensional positions and velocities")

    calls = 0

    def rhs(_t: float, y: Array) -> Array:
        nonlocal calls
        calls += 1
        if calls > MAX_EVALUATIONS:
            raise TooCloseError
        x = y[:6].reshape(3, 2)
        return np.concatenate([y[6:], accelerations(x, m, softening).ravel()])

    times = np.linspace(0.0, duration, frames + 1)
    sol = solve_ivp(
        rhs,
        (0.0, duration),
        np.concatenate([x0.ravel(), v0.ravel()]),
        method="DOP853",
        t_eval=times,
        rtol=tolerance,
        atol=tolerance,
    )
    if not sol.success:
        raise TooCloseError(sol.message)
    xs = sol.y[:6].T.reshape(-1, 3, 2)
    vs = sol.y[6:].T.reshape(-1, 3, 2)
    energies = np.array([energy(xs[k], vs[k], m, softening) for k in range(len(times))])
    return Trajectory(times, xs, energies)


def centre_of_mass_frame(masses: Array, positions: Array, velocities: Array) -> tuple[Array, Array]:
    """Shift positions and velocities so the centre of mass sits still at the origin."""
    m = np.asarray(masses, dtype=np.float64)
    x = np.asarray(positions, dtype=np.float64)
    v = np.asarray(velocities, dtype=np.float64)
    total = m.sum()
    return x - (m @ x) / total, v - (m @ v) / total
