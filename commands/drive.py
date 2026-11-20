"""Default teleop command: field-relative swerve driving from a controller."""

from commands2 import Command
from commands2.button import CommandNiDsXboxController
from wpimath import apply_deadband

from constants import DriveConstants, OIConstants
from subsystems.drivetrain import Drivetrain


def stick_velocities(
    controller: CommandNiDsXboxController,
) -> tuple[float, float, float]:
    """Field-relative (vx m/s, vy m/s, omega rad/s) from the driver's sticks.

    Left stick translates, right stick X rotates. On the HID, forward is -Y and
    left is -X, so each axis is negated to match the field frame (+x fwd, +y left).
    """
    vx = _scaled(controller.get_left_y()) * DriveConstants.MAX_SPEED_MPS
    vy = _scaled(controller.get_left_x()) * DriveConstants.MAX_SPEED_MPS
    omega = _scaled(controller.get_right_x()) * DriveConstants.MAX_ANGULAR_SPEED_RPS
    return vx, vy, omega


def _scaled(raw: float) -> float:
    """Apply a deadband and flip sign into the field frame."""
    return -apply_deadband(raw, OIConstants.DEADBAND)


class DriveByController(Command):
    """Continuously drives the chassis from the driver's joysticks."""

    def __init__(
        self, drivetrain: Drivetrain, controller: CommandNiDsXboxController
    ) -> None:
        super().__init__()
        self._drivetrain = drivetrain
        self._controller = controller
        self.add_requirements(drivetrain)

    def execute(self) -> None:
        self._drivetrain.drive(*stick_velocities(self._controller), field_relative=True)
