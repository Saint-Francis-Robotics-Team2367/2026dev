"""Swerve math + simulation tests (HAL-free, so they run fast anywhere).

These exercise the kinematics -> module -> odometry pipeline directly, without
constructing the Drivetrain subsystem (which pulls in Field2d/HAL). The generated
``robot_test.py`` covers full-robot boot separately.
"""

import math

import pytest
from wpimath import (
    ChassisVelocities,
    Rotation2d,
    SwerveDrive4Odometry,
    SwerveModuleVelocity,
)

from constants import DriveConstants
from subsystems.swervemodule import SwerveModule


def _modules() -> list[SwerveModule]:
    return [SwerveModule(name) for name in ("FL", "FR", "BL", "BR")]


def _positions(modules: list[SwerveModule]):
    return (
        modules[0].get_position(),
        modules[1].get_position(),
        modules[2].get_position(),
        modules[3].get_position(),
    )


def test_forward_command_gives_straight_modules() -> None:
    states = DriveConstants.KINEMATICS.toSwerveModuleVelocities(
        ChassisVelocities(1.0, 0.0, 0.0)
    )
    for state in states:
        assert state.velocity == pytest.approx(1.0, abs=1e-6)
        assert state.angle.radians() == pytest.approx(0.0, abs=1e-6)


def test_module_integrates_distance() -> None:
    module = SwerveModule("test")
    module.set_desired_state(SwerveModuleVelocity(2.0, Rotation2d()))
    for _ in range(50):  # 50 * 0.02s = 1s at 2 m/s
        module.simulate(0.02)
    assert module.get_position().distance == pytest.approx(2.0, abs=1e-6)


def test_optimize_takes_shortest_path() -> None:
    module = SwerveModule("test")  # starts at 0 rad
    # Command 170 deg forward; the optimal move is ~-10 deg with reversed wheel.
    module.set_desired_state(SwerveModuleVelocity(1.0, Rotation2d.fromDegrees(170)))
    state = module.get_state()
    assert abs(state.angle.radians()) <= math.pi / 2  # never rotates more than 90 deg
    assert state.velocity < 0  # wheel reversed instead of spinning the module around


def test_odometry_tracks_forward_drive() -> None:
    modules = _modules()
    odometry = SwerveDrive4Odometry(
        DriveConstants.KINEMATICS, Rotation2d(), _positions(modules)
    )
    states = DriveConstants.KINEMATICS.toSwerveModuleVelocities(
        ChassisVelocities(1.0, 0.0, 0.0)
    )

    pose = odometry.getPose()
    for _ in range(50):  # 1 second at 1 m/s forward
        for module, state in zip(modules, states):
            module.set_desired_state(state)
            module.simulate(0.02)
        pose = odometry.update(Rotation2d(), _positions(modules))

    assert pose.X() == pytest.approx(1.0, abs=0.05)
    assert abs(pose.Y()) < 0.02
