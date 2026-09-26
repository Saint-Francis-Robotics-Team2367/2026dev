"""Default teleop command: field-relative swerve driving from a controller."""

from commands2 import Command
from commands2.button import CommandNiDsXboxController
from wpimath import apply_deadband

from constants import DriveConstants, OIConstants
from subsystems.drivetrain import Drivetrain


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
        # Left stick translates, right stick X rotates. On the HID, forward is
        # -Y and left is -X, so negate to match the field frame (+x fwd, +y left).
        vx = self._scaled(self._controller.get_left_y()) * DriveConstants.MAX_SPEED_MPS
        vy = self._scaled(self._controller.get_left_x()) * DriveConstants.MAX_SPEED_MPS
        omega = (
            self._scaled(self._controller.get_right_x())
            * DriveConstants.MAX_ANGULAR_SPEED_RPS
        )
        self._drivetrain.drive(vx, vy, omega, field_relative=True)

    @staticmethod
    def _scaled(raw: float) -> float:
        """Apply a deadband and flip sign into the field frame."""
        return -apply_deadband(raw, OIConstants.DEADBAND)
