import numpy as np
import pytest
from pydantic import ValidationError

from threebody import physics
from threebody.config import SetupConfig
from threebody.physics import accelerations, simulate
from threebody.presets import LAGRANGE_TRIANGLE, PRESETS


def _arrays(cfg: SetupConfig):
    return np.array(cfg.masses), np.array(cfg.positions), np.array(cfg.velocities)


PERIODIC = {name: p for name, p in PRESETS.items() if p.period is not None}


@pytest.mark.parametrize("name", list(PERIODIC))
def test_every_periodic_preset_closes_after_one_period(name):
    preset = PERIODIC[name]
    assert preset.period is not None
    m, x, v = _arrays(preset.config)
    traj = simulate(m, x, v, duration=preset.period, frames=50)
    # The published values have six digits; that is enough to come back within a few thousandths.
    assert np.max(np.abs(traj.positions[-1] - x)) < 5e-3, name


@pytest.mark.parametrize("name", list(PRESETS))
def test_every_preset_runs_and_keeps_its_energy(name):
    traj = PRESETS[name].config.run()
    assert traj.positions.shape[1:] == (3, 2)
    assert np.all(np.isfinite(traj.positions))
    assert traj.energy_drift < 1e-5


def test_momentum_is_conserved():
    m, x, _ = _arrays(LAGRANGE_TRIANGLE)
    a = accelerations(x, m, softening=0.0)
    # Newton's third law: the forces of the three bodies sum to zero.
    assert np.allclose(m @ a, 0.0, atol=1e-12)


def test_lagrange_triangle_keeps_its_shape():
    m, x, v = _arrays(LAGRANGE_TRIANGLE)
    traj = simulate(m, x, v, duration=5.0)
    last = traj.positions[-1]
    sides = [np.linalg.norm(last[i] - last[(i + 1) % 3]) for i in range(3)]
    assert np.ptp(sides) < 1e-6


def test_a_head_on_collision_finishes_quickly():
    traj = simulate(
        np.ones(3), np.array([[-1.0, 0.0], [1.0, 0.0], [0.0, 5.0]]), np.zeros((3, 2)), duration=10
    )
    assert np.all(np.isfinite(traj.positions))


def test_a_runaway_computation_is_stopped(monkeypatch):
    monkeypatch.setattr(physics, "MAX_EVALUATIONS", 100)
    with pytest.raises(physics.TooCloseError):
        PRESETS["Butterfly IV"].config.run()


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
