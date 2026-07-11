"""Robot-wide constants: swerve geometry, kinematics, limits, and controls.

All values are documented PLACEHOLDERS (MK4i-style module) chosen so simulation
behaves sensibly. Replace with measured / tuned numbers for the real robot.
Units follow the WPILib standard: meters, radians, seconds (so speeds are m/s
and rad/s).
"""

import math

from wpimath import SwerveDrive4Kinematics, Translation2d


class DriveConstants:
    """Chassis geometry, kinematics, and speed limits."""

    # Distance between the centers of the left and right wheels, and between the
    # front and back wheels. Assumed square here — measure the real robot.
    TRACK_WIDTH_M = 0.5
    WHEEL_BASE_M = 0.5

    _HALF_TRACK = TRACK_WIDTH_M / 2
    _HALF_BASE = WHEEL_BASE_M / 2

    # Module locations relative to robot center. WPILib convention: +x forward,
    # +y to the left. Order used everywhere below: FL, FR, BL, BR.
    FRONT_LEFT_LOCATION = Translation2d(_HALF_BASE, _HALF_TRACK)
    FRONT_RIGHT_LOCATION = Translation2d(_HALF_BASE, -_HALF_TRACK)
    BACK_LEFT_LOCATION = Translation2d(-_HALF_BASE, _HALF_TRACK)
    BACK_RIGHT_LOCATION = Translation2d(-_HALF_BASE, -_HALF_TRACK)

    KINEMATICS = SwerveDrive4Kinematics(
        FRONT_LEFT_LOCATION,
        FRONT_RIGHT_LOCATION,
        BACK_LEFT_LOCATION,
        BACK_RIGHT_LOCATION,
    )

    # Max attainable module wheel speed; used to desaturate wheel velocities.
    MAX_SPEED_MPS = 4.5
    # Max chassis rotation rate (one full rotation per second).
    MAX_ANGULAR_SPEED_RPS = 2 * math.pi


class ModuleConstants:
    """Per-module hardware description (documented for when real motors land)."""

    WHEEL_DIAMETER_M = 0.1016  # 4 in
    DRIVE_GEAR_RATIO = 6.75  # MK4i L2 drive reduction
    TURN_GEAR_RATIO = 150.0 / 7.0  # MK4i steering reduction


class HardwareIds:
    """Placeholder CAN IDs / channels — unused until vendordep motors exist.

    Kept here so wiring is documented in one place. Order: FL, FR, BL, BR.
    """

    DRIVE_MOTOR_CAN = (1, 3, 5, 7)
    TURN_MOTOR_CAN = (2, 4, 6, 8)
    TURN_ENCODER_CAN = (9, 10, 11, 12)


class OIConstants:
    """Operator interface (driver controls)."""

    DRIVER_CONTROLLER_PORT = 0
    # Ignore small joystick noise near center.
    DEADBAND = 0.1
