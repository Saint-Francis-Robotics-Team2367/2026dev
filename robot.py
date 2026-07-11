"""2027 FRC robot — command-based entry point.

Run in the WPILib Simulation GUI with:  robotpy sim
Run the headless smoke tests with:      robotpy test
"""

import commands2

from robotcontainer import RobotContainer


class MyRobot(commands2.TimedCommandRobot):
    """Main robot class.

    ``TimedCommandRobot`` runs the ``CommandScheduler`` every periodic loop for
    us, so all we do here is build the ``RobotContainer`` that wires up the
    subsystems, default commands, and button bindings, then schedule the
    autonomous command when Autonomous starts.

    Note: 2027 removed ``robotInit`` — setup happens in the constructor.
    """

    def __init__(self) -> None:
        super().__init__()
        self.container = RobotContainer()
        self._auto_command: commands2.Command | None = None

    def autonomousInit(self) -> None:
        self._auto_command = self.container.get_autonomous_command()
        self._auto_command.schedule()

    def teleopInit(self) -> None:
        # Stop the autonomous routine so it doesn't fight the teleop drive command.
        if self._auto_command is not None:
            self._auto_command.cancel()
