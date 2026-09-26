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

import pytest
from wpilib.simulation import DriverStationSim
from wpimath import Rotation2d, SwerveModuleVelocity

from subsystems.swervemodule import SwerveModule

_LOOP_S = 0.01
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


def _run(module: SwerveModule, desired: SwerveModuleVelocity, seconds: float) -> None:
    """Command ``desired`` and advance physics in real time for ``seconds``."""
    last = time.monotonic()
    end = last + seconds
    while (now := time.monotonic()) < end:
        DriverStationSim.notify_new_data()
        module.set_desired_state(desired)
        module.simulate(now - last)
        last = now
        time.sleep(_LOOP_S)


def test_drive_reaches_commanded_velocity() -> None:
    module = _module()
    _run(module, SwerveModuleVelocity(2.0, Rotation2d()), 1.5)
    state = module.get_state()
    assert state.velocity == pytest.approx(2.0, abs=0.15)
    assert state.angle.degrees() == pytest.approx(0.0, abs=3.0)


def test_steer_reaches_commanded_angle() -> None:
    module = _module()
    _run(module, SwerveModuleVelocity(0.5, Rotation2d.from_degrees(60)), 1.5)
    assert module.get_state().angle.degrees() == pytest.approx(60.0, abs=3.0)


def test_steer_takes_shortest_path() -> None:
    module = _module()
    _run(module, SwerveModuleVelocity(1.0, Rotation2d.from_degrees(170)), 1.5)
    state = module.get_state()
    # Turned ~-10 deg and reversed the wheel instead of spinning 170 deg around.
    assert state.angle.degrees() == pytest.approx(-10.0, abs=3.0)
    assert state.velocity < -0.5


def test_distance_matches_velocity() -> None:
    module = _module()
    desired = SwerveModuleVelocity(1.0, Rotation2d())
    _run(module, desired, 1.0)  # spin up
    start = module.get_position().distance
    t0 = time.monotonic()
    _run(module, desired, 1.0)
    elapsed = time.monotonic() - t0
    assert module.get_position().distance - start == pytest.approx(
        1.0 * elapsed, rel=0.1
    )


def test_encoder_offset_reads_physical_angle() -> None:
    # With a magnet offset configured, the module must still steer to the true
    # physical angle (the sim models the offset like the real CANcoder does).
    module = _module(offset_rot=0.3)
    _run(module, SwerveModuleVelocity(0.5, Rotation2d.from_degrees(45)), 1.5)
    assert module.get_state().angle.degrees() == pytest.approx(45.0, abs=3.0)
    assert module._steer_sim.get_angular_position() == pytest.approx(
        math.radians(45.0), abs=math.radians(3.0)
    )
