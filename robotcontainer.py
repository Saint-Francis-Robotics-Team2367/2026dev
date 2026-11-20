"""Wires the robot together: subsystems, default commands, and button bindings.

Kept separate from ``robot.py`` (the standard command-based pattern) so the robot
lifecycle and the wiring can evolve independently.
"""

import commands2
from commands2.button import CommandNiDsXboxController

from commands.align import AlignToTag
from commands.auto import demo_auto
from commands.drive import DriveByController
from constants import OIConstants
from subsystems.drivetrain import Drivetrain
from subsystems.questnav_subsystem import QuestNavSubsystem


class RobotContainer:
    """Declarative container for subsystems and operator controls."""

    def __init__(self) -> None:
        self.drivetrain = Drivetrain()
        # Registered after the drivetrain, so each loop odometry updates first and
        # QuestNav frames are fused into the fresh estimate.
        self.questnav = QuestNavSubsystem(self.drivetrain)
        self.driver_controller = CommandNiDsXboxController(
            OIConstants.DRIVER_CONTROLLER_PORT
        )

        # Teleop default: drive field-relative from the driver's sticks.
        self.drivetrain.set_default_command(
            DriveByController(self.drivetrain, self.driver_controller)
        )
        self.configure_bindings()

    def configure_bindings(self) -> None:
        """Bind operator controls to commands."""
        # Hold A: drive to 1 m in front of the target AprilTag and hold there.
        # Release to get the sticks back (the default command resumes).
        self.align_command = AlignToTag(
            self.drivetrain, self.questnav, self.driver_controller
        )
        self.driver_controller.a().while_true(self.align_command)

    def get_autonomous_command(self) -> commands2.Command:
        """The routine that runs in Autonomous (scheduled by robot.py)."""
        return demo_auto(self.drivetrain)
