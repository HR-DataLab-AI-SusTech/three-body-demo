import numpy as np
import pytest
from pydantic import ValidationError

from threebody.config import SetupConfig
from threebody.physics import accelerations, simulate
from threebody.presets import FIGURE_EIGHT, FIGURE_EIGHT_PERIOD, LAGRANGE_TRIANGLE, PRESETS


def _arrays(cfg: SetupConfig):
    return np.array(cfg.masses), np.array(cfg.positions), np.array(cfg.velocities)


def test_figure_eight_closes_after_one_period():
    m, x, v = _arrays(FIGURE_EIGHT)
    traj = simulate(m, x, v, duration=FIGURE_EIGHT_PERIOD, dt=1e-3, softening=0.0)
    assert np.max(np.abs(traj.positions[-1] - x)) < 1e-2


def test_energy_stays_put_with_verlet():
    m, x, v = _arrays(FIGURE_EIGHT)
    traj = simulate(m, x, v, duration=3 * FIGURE_EIGHT_PERIOD, dt=1e-3, softening=0.0)
    assert traj.energy_drift < 1e-6


def test_momentum_is_conserved():
    m, x, _ = _arrays(LAGRANGE_TRIANGLE)
    a = accelerations(x, m, softening=0.0)
    # Newton's third law: the forces of the three bodies sum to zero.
    assert np.allclose(m @ a, 0.0, atol=1e-12)


def test_lagrange_triangle_keeps_its_shape():
    m, x, v = _arrays(LAGRANGE_TRIANGLE)
    traj = simulate(m, x, v, duration=5.0, dt=1e-3, softening=0.0)
    last = traj.positions[-1]
    sides = [np.linalg.norm(last[i] - last[(i + 1) % 3]) for i in range(3)]
    assert np.ptp(sides) < 1e-3


@pytest.mark.parametrize("name", list(PRESETS))
def test_every_preset_runs(name):
    traj = PRESETS[name].run(frames=50)
    assert traj.positions.shape[1:] == (3, 2)
    assert np.all(np.isfinite(traj.positions))


def test_a_public_form_cannot_ask_for_absurd_values():
    with pytest.raises(ValidationError):
        SetupConfig(
            masses=(1e9, 1.0, 1.0),
            positions=((0, 0), (1, 0), (0, 1)),
            velocities=((0, 0), (0, 0), (0, 0)),
        )
    with pytest.raises(ValidationError):
        SetupConfig.model_validate(
            {
                "masses": (1, 1, 1),
                "positions": ((0, 0), (1, 0), (0, 1)),
                "velocities": ((0, 0), (0, 0), (0, 0)),
                "duration": 10_000,
            }
        )
