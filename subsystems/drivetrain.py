"""Swerve drivetrain subsystem: modules, odometry, and the Field2d widget.

In simulation this subsystem also owns the robot heading. SystemCore has an
onboard IMU, but with no gyro wired in sim we integrate heading from the
commanded rotational velocity — good enough for an idealized model. Swap in the
real IMU angle here once hardware exists.
"""

import commands2
import wpilib
from wpimath import (
    ChassisVelocities,
    Pose2d,
    Rotation2d,
    SwerveDrive4Odometry,
    SwerveModulePosition,
    SwerveModuleVelocity,
)

from constants import DriveConstants
from subsystems.swervemodule import SwerveModule
from telemetry import DrivetrainTelemetry

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
        self._modules = [SwerveModule(name) for name in ("FL", "FR", "BL", "BR")]
        self._heading = Rotation2d()
        self._commanded_omega_rps: float = 0.0

        self._odometry = SwerveDrive4Odometry(
            DriveConstants.KINEMATICS,
            self._heading,
            self._module_positions(),
            Pose2d(),
        )

        self._field = wpilib.Field2d()
        wpilib.SmartDashboard.putData("Field", self._field)
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
            velocities = velocities.toRobotRelative(self._heading)
        # Compensate for translational skew while translating and rotating.
        velocities = velocities.discretize(_PERIOD_S)
        self._commanded_omega_rps = omega

        states = DriveConstants.KINEMATICS.toSwerveModuleVelocities(velocities)
        states = DriveConstants.KINEMATICS.desaturateWheelVelocities(
            states, DriveConstants.MAX_SPEED_MPS
        )
        for module, state in zip(self._modules, states):
            module.set_desired_state(state)

    def get_pose(self) -> Pose2d:
        return self._odometry.getPose()

    def periodic(self) -> None:
        pose = self._odometry.update(self._heading, self._module_positions())
        self._field.setRobotPose(pose)
        states = self._module_states()
        chassis = DriveConstants.KINEMATICS.toChassisVelocities(states)
        self._telemetry.publish(pose, chassis, states)

    def simulationPeriodic(self) -> None:
        # Integrate heading from the last commanded rotation, and advance each
        # module's wheel distance. Idealized: modules track commands exactly.
        self._heading = self._heading.rotateBy(
            Rotation2d(self._commanded_omega_rps * _PERIOD_S)
        )
        for module in self._modules:
            module.simulate(_PERIOD_S)
