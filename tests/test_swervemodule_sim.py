"""Phoenix-backed SwerveModule against Phoenix's simulated TalonFX / CANcoder.

These run the module's real code path — device configs, unit conversions, the
Talons' own closed loops — with ``DCMotorSim`` physics. Phoenix's simulated devices
run on wall-clock time, so each test drives the module in real time (~1-2 s each);
stepped/fast-forwarded sim time would starve the device firmware.

Phoenix takes its enable from WPILib's Driver Station whenever WPILib is present,
so the loop enables the *simulated* Driver Station. (``phoenix6.unmanaged.feed_enable``
is for non-WPILib programs like ``bench/bench.py``; here it fights the DS, which reports
disabled, and the motors cut out intermittently.)
"""

import itertools
import math
import time
from collections.abc import Callable

import pytest
from wpilib.simulation import DriverStationSim
from wpimath import Rotation2d, SwerveModuleVelocity

from subsystems.swervemodule import SwerveModule

_LOOP_S = 0.01
_TIMEOUT_S = 6.0  # generous: only a loaded machine gets near it
_SETTLE_S = (
    0.2  # condition must hold this long, so a mid-move pass-through isn't enough
)
# Phoenix sim devices persist for the whole process, so every test gets fresh IDs.
_ids = itertools.count(20, 3)  # CAN IDs must stay within 0-62


@pytest.fixture(autouse=True)
def _enabled():
    DriverStationSim.set_enabled(True)
    DriverStationSim.notify_new_data()
    yield
    DriverStationSim.set_enabled(False)
    DriverStationSim.notify_new_data()


def _module(offset_rot: float = 0.0) -> SwerveModule:
    drive_id = next(_ids)
    return SwerveModule("test", drive_id, drive_id + 1, drive_id + 2, offset_rot)


def _run_until(
    module: SwerveModule,
    desired: SwerveModuleVelocity,
    reached: Callable[[], bool],
    timeout_s: float = _TIMEOUT_S,
) -> None:
    """Command ``desired`` and advance physics in real time until ``reached()`` has
    held for ``_SETTLE_S`` (or ``timeout_s`` passes; the caller's asserts then fail).

    Phoenix's sim runs on wall-clock time, so a loaded machine slows convergence;
    waiting on the condition instead of a fixed duration keeps the tests deterministic.
    """
    last = time.monotonic()
    end = last + timeout_s
    held_since: float | None = None
    while (now := time.monotonic()) < end:
        DriverStationSim.notify_new_data()
        module.set_desired_state(desired)
        module.simulate(now - last)
        last = now
        if reached():
            held_since = held_since if held_since is not None else now
            if now - held_since >= _SETTLE_S:
                return
        else:
            held_since = None
        time.sleep(_LOOP_S)


def _run_for(
    module: SwerveModule, desired: SwerveModuleVelocity, seconds: float
) -> None:
    """Command ``desired`` and advance physics in real time for exactly ``seconds``."""
    _run_until(module, desired, lambda: False, seconds)


def _near(
    actual: Callable[[], float], expected: float, tol: float
) -> Callable[[], bool]:
    return lambda: abs(actual() - expected) <= tol


def test_drive_reaches_commanded_velocity() -> None:
    module = _module()
    desired = SwerveModuleVelocity(2.0, Rotation2d())
    _run_until(module, desired, _near(lambda: module.get_state().velocity, 2.0, 0.15))
    state = module.get_state()
    assert state.velocity == pytest.approx(2.0, abs=0.15)
    assert state.angle.degrees() == pytest.approx(0.0, abs=3.0)


def test_steer_reaches_commanded_angle() -> None:
    module = _module()
    desired = SwerveModuleVelocity(0.5, Rotation2d.from_degrees(60))
    _run_until(
        module, desired, _near(lambda: module.get_state().angle.degrees(), 60.0, 3.0)
    )
    assert module.get_state().angle.degrees() == pytest.approx(60.0, abs=3.0)


def test_steer_takes_shortest_path() -> None:
    module = _module()
    desired = SwerveModuleVelocity(1.0, Rotation2d.from_degrees(170))
    _run_until(
        module,
        desired,
        lambda: abs(module.get_state().angle.degrees() + 10.0) <= 3.0
        and module.get_state().velocity < -0.5,
    )
    state = module.get_state()
    # Turned ~-10 deg and reversed the wheel instead of spinning 170 deg around.
    assert state.angle.degrees() == pytest.approx(-10.0, abs=3.0)
    assert state.velocity < -0.5


def test_distance_matches_velocity() -> None:
    module = _module()
    desired = SwerveModuleVelocity(1.0, Rotation2d())
    # Spin up until settled at the commanded velocity.
    _run_until(module, desired, _near(lambda: module.get_state().velocity, 1.0, 0.1))
    start = module.get_position().distance
    # Integrate the module's own velocity reading over the window. Comparing against
    # commanded velocity x wall time is flaky: a starved Phoenix thread under load
    # changes the speed mid-window, but distance must still track what it reported.
    integrated = 0.0
    last = time.monotonic()

    def accumulate() -> bool:
        nonlocal integrated, last
        now = time.monotonic()
        integrated += module.get_state().velocity * (now - last)
        last = now
        return False

    _run_until(module, desired, accumulate, 1.0)
    assert integrated > 0.2  # it actually moved
    assert module.get_position().distance - start == pytest.approx(integrated, rel=0.25)


def test_encoder_offset_reads_physical_angle() -> None:
    # With a magnet offset configured, the module must still steer to the true
    # physical angle (the sim models the offset like the real CANcoder does).
    module = _module(offset_rot=0.3)
    desired = SwerveModuleVelocity(0.5, Rotation2d.from_degrees(45))
    _run_until(
        module, desired, _near(lambda: module.get_state().angle.degrees(), 45.0, 3.0)
    )
    assert module.get_state().angle.degrees() == pytest.approx(45.0, abs=3.0)
    assert module._steer_sim.get_angular_position() == pytest.approx(
        math.radians(45.0), abs=math.radians(3.0)
    )
