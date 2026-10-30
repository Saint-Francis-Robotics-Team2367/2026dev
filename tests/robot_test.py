"""
This test module imports tests that come with wpilib, and can be used
to test basic functionality of just about any robot.

RobotPy's own ``test_opmode`` only drives published opmodes, and a
``TimedRobot`` publishes none, so Utility mode gets its own boot test below.
"""

import commands2
from hal import RobotMode
from wpilib.simulation import DriverStationSim, step_timing

from wpilib.testing.robot_tests import *


def test_utility_mode(control, robot) -> None:
    """Boots, enters Utility mode, and checks the spin test starts while QuestNav runs.

    The spin sequence runs on wall-clock time, so it barely advances while the sim
    fast-forwards; ``tests/test_debug.py`` covers the sequence itself.
    """
    questnav = robot.container.questnav
    calls = 0
    original_periodic = questnav.periodic

    def counting_periodic() -> None:
        nonlocal calls
        calls += 1
        original_periodic()

    questnav.periodic = counting_periodic

    with control.run_robot():
        control.step_timing(seconds=0.5, autonomous=False, enabled=False)

        DriverStationSim.set_robot_mode(RobotMode.UTILITY)
        DriverStationSim.set_enabled(True)
        before = calls
        for _ in range(10):  # 2 s of simulated time
            DriverStationSim.notify_new_data()
            step_timing(0.2)
            assert control.robot_is_alive

        spin = robot._spin_command
        assert spin is not None, "utility_init never ran"
        assert commands2.CommandScheduler.get_instance().is_scheduled(spin)
        assert calls - before >= 50  # ~20 ms loop: QuestNav kept running

        control.step_timing(seconds=0.5, autonomous=False, enabled=False)
