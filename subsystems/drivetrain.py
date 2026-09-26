"""Swerve drivetrain subsystem: modules, odometry, and the Field2d widget.

In simulation this subsystem also owns the robot heading. SystemCore has an
onboard IMU, but with no gyro wired in sim we integrate heading from the
rotation rate the modules actually produce (forward kinematics of their measured
states). Swap in the real IMU angle here once hardware exists.
"""

import commands2
import telemetry
import wpilib
from wpimath import (
    ChassisVelocities,
    Pose2d,
    Rotation2d,
    SwerveDrive4Odometry,
    SwerveModulePosition,
    SwerveModuleVelocity,
)

from constants import DriveConstants, HardwareIds
from subsystems.swervemodule import SwerveModule
from drivetrain_telemetry import DrivetrainTelemetry

# Robot main-loop period; module/heading integration uses this in simulation.
_PERIOD_S = 0.02

_ModulePositions = tuple[
    SwerveModulePosition,
    SwerveModulePosition,
    SwerveModulePosition,
    SwerveModulePosition,
]

_ModuleStates = tuple[
    SwerveModuleVelocity,
    SwerveModuleVelocity,
    SwerveModuleVelocity,
    SwerveModuleVelocity,
]


class Drivetrain(commands2.Subsystem):
    def __init__(self) -> None:
        super().__init__()
        self._modules = [
            SwerveModule(
                name,
                HardwareIds.DRIVE_MOTOR_CAN[i],
                HardwareIds.TURN_MOTOR_CAN[i],
                HardwareIds.TURN_ENCODER_CAN[i],
                HardwareIds.TURN_ENCODER_OFFSETS_ROT[i],
                HardwareIds.CAN_BUS,
                HardwareIds.DRIVE_INVERTED[i],
            )
            for i, name in enumerate(("FL", "FR", "BL", "BR"))
        ]
        self._heading = Rotation2d()

        self._odometry = SwerveDrive4Odometry(
            DriveConstants.KINEMATICS,
            self._heading,
            self._module_positions(),
            Pose2d(),
        )

        self._field = wpilib.Field2d()
        self._telemetry = DrivetrainTelemetry()

    def _module_positions(self) -> _ModulePositions:
        return (
            self._modules[0].get_position(),
            self._modules[1].get_position(),
            self._modules[2].get_position(),
            self._modules[3].get_position(),
        )

    def _module_states(self) -> _ModuleStates:
        return (
            self._modules[0].get_state(),
            self._modules[1].get_state(),
            self._modules[2].get_state(),
            self._modules[3].get_state(),
        )

    def drive(
        self, vx: float, vy: float, omega: float, field_relative: bool = True
    ) -> None:
        """Drive the chassis. vx/vy are m/s, omega is rad/s (CCW positive)."""
        velocities = ChassisVelocities(vx, vy, omega)
        if field_relative:
            velocities = velocities.to_robot_relative(self._heading)
        # Compensate for translational skew while translating and rotating.
        velocities = velocities.discretize(_PERIOD_S)

        states = DriveConstants.KINEMATICS.to_swerve_module_velocities(velocities)
        states = DriveConstants.KINEMATICS.desaturate_wheel_velocities(
            states, DriveConstants.MAX_SPEED_MPS
        )
        for module, state in zip(self._modules, states):
            module.set_desired_state(state)

    def get_pose(self) -> Pose2d:
        return self._odometry.get_pose()

    def periodic(self) -> None:
        pose = self._odometry.update(self._heading, self._module_positions())
        self._field.set_robot_pose(pose)
        telemetry.log("Field", self._field)
        states = self._module_states()
        chassis = DriveConstants.KINEMATICS.to_chassis_velocities(states)
        self._telemetry.publish(pose, chassis, states)

    def simulation_periodic(self) -> None:
        # Advance each module's motor physics, then integrate heading from the
        # rotation rate the modules actually produce (stand-in for the IMU).
        for module in self._modules:
            module.simulate(_PERIOD_S)
        omega = DriveConstants.KINEMATICS.to_chassis_velocities(
            self._module_states()
        ).omega
        self._heading = self._heading.rotate_by(Rotation2d(omega * _PERIOD_S))
