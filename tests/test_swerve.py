"""Swerve math tests (HAL-free, so they run fast anywhere).

These exercise kinematics, module-state optimization, and odometry with pure
wpimath types. The Phoenix-backed ``SwerveModule`` is covered in real time by
``test_swervemodule_sim.py``; ``robot_test.py`` covers full-robot boot.
"""

import math

import pytest
from wpimath import (
    ChassisVelocities,
    Rotation2d,
    SwerveDrive4Odometry,
    SwerveModulePosition,
    SwerveModuleVelocity,
)

from constants import DriveConstants


def test_forward_command_gives_straight_modules() -> None:
    states = DriveConstants.KINEMATICS.to_swerve_module_velocities(
        ChassisVelocities(1.0, 0.0, 0.0)
    )
    for state in states:
        assert state.velocity == pytest.approx(1.0, abs=1e-6)
        assert state.angle.radians() == pytest.approx(0.0, abs=1e-6)


def test_optimize_takes_shortest_path() -> None:
    # Module at 0 rad commanded to 170 deg: the optimal move is ~-10 deg with the
    # wheel reversed, never a 170 deg spin.
    optimized = SwerveModuleVelocity(1.0, Rotation2d.from_degrees(170)).optimize(
        Rotation2d()
    )
    assert abs(optimized.angle.radians()) <= math.pi / 2
    assert optimized.velocity < 0


def _positions(distance_m: float):
    """All four modules pointed straight ahead at the same wheel distance."""
    p = SwerveModulePosition(distance_m, Rotation2d())
    return (p, p, p, p)


def test_odometry_tracks_forward_drive() -> None:
    odometry = SwerveDrive4Odometry(
        DriveConstants.KINEMATICS, Rotation2d(), _positions(0.0)
    )
    pose = odometry.get_pose()
    for step in range(1, 51):  # 1 second at 1 m/s forward, all wheels straight
        pose = odometry.update(Rotation2d(), _positions(step * 0.02))

    assert pose.x == pytest.approx(1.0, abs=0.05)
    assert abs(pose.y) < 0.02
