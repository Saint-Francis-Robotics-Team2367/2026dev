"""2027 FRC robot — command-based entry point.

Run in the WPILib Simulation GUI with:  robotpy sim
Run the headless smoke tests with:      robotpy test
"""

import commands2
import wpilib

from commands.debug import SpinAllMotors
from dslog import log
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
        self._spin_command: commands2.Command | None = None
        self._last_ds_state: tuple | None = None
        log("[robot] code started")

    def robot_periodic(self) -> None:
        # Log every DS state change so a mode that never starts is visible.
        state = (
            wpilib.DriverStationBackend.is_ds_attached(),
            wpilib.DriverStationBackend.is_enabled(),
            wpilib.DriverStationBackend.get_robot_mode(),
            wpilib.DriverStationBackend.get_opmode(),
        )
        if state != self._last_ds_state:
            self._last_ds_state = state
            attached, enabled, mode, opmode = state
            log(
                f"[robot] DS attached={attached} enabled={enabled} "
                f"mode={mode} opmode={opmode!r}"
            )

    def driver_station_connected(self) -> None:
        log("[robot] driver station connected")

    def autonomous_init(self) -> None:
        log("[robot] autonomous")
        self._auto_command = self.container.get_autonomous_command()
        self._auto_command.schedule()

    def teleop_init(self) -> None:
        log("[robot] teleop")
        # Stop the autonomous routine so it doesn't fight the teleop drive command.
        if self._auto_command is not None:
            self._auto_command.cancel()

    def disabled_init(self) -> None:
        log("[robot] disabled")

    def utility_init(self) -> None:
        # Bring-up: spin each motor in turn, no joystick; watch the Driver Station console.
        log("[robot] utility mode: spinning all drive/steer motors")
        self._spin_command = SpinAllMotors(self.container.drivetrain)
        self._spin_command.schedule()

    def utility_exit(self) -> None:
        if self._spin_command is not None:
            self._spin_command.cancel()
