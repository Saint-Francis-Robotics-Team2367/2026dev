"""The bring-up spin command and DS console logging (no motion; sequencing only).

Phoenix's simulated devices have no physics here, so these check that the command steps
through all eight motors and finishes, not that anything spins.
"""

import time

import pytest
from wpilib.simulation import DriverStationSim

import commands.debug as debug
import dslog
from commands.debug import SpinAllMotors
from constants import DebugConstants
from subsystems.drivetrain import Drivetrain


@pytest.fixture(autouse=True)
def _enabled():
    DriverStationSim.set_enabled(True)
    DriverStationSim.notify_new_data()
    yield
    DriverStationSim.set_enabled(False)
    DriverStationSim.notify_new_data()


def test_log_goes_to_driver_station_console(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[str] = []
    monkeypatch.setattr(dslog.hal, "send_console_line", lambda line: sent.append(line))
    dslog.log("[test] hello")
    assert sent == ["[test] hello"]


def test_spin_all_motors_runs_each_motor_then_finishes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines: list[str] = []
    monkeypatch.setattr(debug, "log", lines.append)
    monkeypatch.setattr(DebugConstants, "SPIN_SECONDS", 0.05)

    command = SpinAllMotors(Drivetrain())
    command.initialize()
    deadline = time.monotonic() + 10.0
    while not command.is_finished() and time.monotonic() < deadline:
        DriverStationSim.notify_new_data()
        command.execute()
        time.sleep(0.01)
    # ``is_finished`` is snake_case; a camelCase override never runs in 2027.
    assert command.is_finished()
    command.end(False)

    starts = [line for line in lines if line.startswith("[spin] (")]
    assert [line.split(")")[0] for line in starts] == [
        f"[spin] ({i}/8" for i in range(1, 9)
    ]
    summary = [line for line in lines if line.split(" ")[1:2] in (["OK"], ["FAIL"])]
    assert len(summary) == 8
