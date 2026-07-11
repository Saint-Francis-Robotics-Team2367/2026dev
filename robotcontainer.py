"""Wires the robot together: subsystems, default commands, and button bindings.

Kept separate from ``robot.py`` (the standard command-based pattern) so the robot
lifecycle and the wiring can evolve independently.
"""

import commands2
from commands2.button import CommandNiDsXboxController

from commands.auto import demo_auto
from commands.drive import DriveByController
from constants import OIConstants
from subsystems.drivetrain import Drivetrain


class RobotContainer:
    """Declarative container for subsystems and operator controls."""

    def __init__(self) -> None:
        self.drivetrain = Drivetrain()
        self.driver_controller = CommandNiDsXboxController(
            OIConstants.DRIVER_CONTROLLER_PORT
        )

        # Teleop default: drive field-relative from the driver's sticks.
        self.drivetrain.setDefaultCommand(
            DriveByController(self.drivetrain, self.driver_controller)
        )
        self.configure_bindings()

    def configure_bindings(self) -> None:
        """Bind operator controls to commands. Empty until we add buttons."""

    def get_autonomous_command(self) -> commands2.Command:
        """The routine that runs in Autonomous (scheduled by robot.py)."""
        return demo_auto(self.drivetrain)
