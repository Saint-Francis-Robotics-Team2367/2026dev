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
    """Per-module hardware: Kraken X60 drive + steer TalonFX, CANcoder on the steer axis.

    Gains are Phoenix 6 units in *mechanism* rotations (the Talon applies the gear
    ratio via SensorToMechanismRatio / RotorToSensorRatio): drive in wheel rotations,
    steer in module rotations. Starting points that behave in simulation — tune on
    the real robot. Per-module wiring (IDs, drive inversion, encoder offsets) lives in
    ``HardwareIds``.
    """

    WHEEL_DIAMETER_M = 0.1016  # 4 in
    WHEEL_CIRCUMFERENCE_M = math.pi * WHEEL_DIAMETER_M
    # MK4i L2 drive reduction (motor rotations per wheel rotation).
    DRIVE_GEAR_RATIO = 6.75
    # MK4i steering reduction. Bench-measured 21.4-21.5 motor rot per module rot.
    TURN_GEAR_RATIO = 150.0 / 7.0

    # Drive velocity loop (VelocityVoltage), volts per wheel rotation/s.
    # Kraken X60 free speed ~100 rotor rps at 12 V -> ~0.12 V/rotor-rps, times the ratio.
    DRIVE_KS = 0.0
    DRIVE_KV = 0.12 * DRIVE_GEAR_RATIO
    DRIVE_KP = 0.5
    # Steer position loop (PositionVoltage, continuous wrap), volts per module rotation.
    STEER_KP = 60.0
    STEER_KD = 0.5

    # Bench-confirmed: with the factory (CCW-positive) setting, +V on every steer motor
    # turns its CANcoder negative, so steer must be clockwise-positive to match the
    # sensor. Also what the 2026 robot had saved on all four steer Talons.
    STEER_INVERTED = True
    # Field-oriented control (FOC) is a Phoenix Pro-licensed feature; leave off unless the
    # motors are licensed.
    USE_FOC = False
    # Current limits from the 2026 robot's saved configs (bench/config_backup.json).
    DRIVE_STATOR_LIMIT_A = 80.0
    DRIVE_SUPPLY_LIMIT_A = 40.0
    STEER_STATOR_LIMIT_A = 55.0
    STEER_SUPPLY_LIMIT_A = 20.0

    # Simulation-only mechanism inertias (kg*m^2) for the DCMotorSim physics model.
    DRIVE_SIM_MOI = 0.025
    STEER_SIM_MOI = 0.004


class HardwareIds:
    """CAN wiring in one place. Order everywhere: FL, FR, BL, BR.

    Bench-identified modules (steer, drive, CANcoder): A = (1, 2, 3), B = (5, 4, 6),
    C = (7, 8, 9), D = (11, 10, 12). The corner assignment below is PROVISIONAL
    (A/B left, C/D right, inferred from drive inversion) until confirmed on the robot.
    """

    # "" = the platform default bus (can_s2 on SystemCore, any CANivore on Windows);
    # set to the CANivore's name if the drivetrain lives on one.
    CAN_BUS = "Drivetrain"  # CANivore name, as shown in Phoenix Tuner X
    #                 FL(A)  FR(C)  BL(B)  BR(D)
    DRIVE_MOTOR_CAN = (2, 8, 4, 10)
    TURN_MOTOR_CAN = (1, 7, 5, 11)
    TURN_ENCODER_CAN = (3, 9, 6, 12)
    # True = clockwise-positive. From the 2026 robot's saved configs (sensors can't
    # tell which way is "forward") -- verify with the first drive test.
    DRIVE_INVERTED = (False, True, False, True)
    # CANcoder magnet offsets (rotations) so each module reads 0 pointing straight
    # forward. These are the offsets the 2026 robot had saved on each CANcoder; the
    # robot code writes them back at startup, so they must stay correct here.
    TURN_ENCODER_OFFSETS_ROT = (
        -0.197021484375,
        -0.165283203125,
        -0.3271484375,
        -0.299072265625,
    )


class OIConstants:
    """Operator interface (driver controls)."""

    DRIVER_CONTROLLER_PORT = 0
    # Ignore small joystick noise near center.
    DEADBAND = 0.1
