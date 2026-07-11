"""Autonomous routines.

``demo_auto`` is a controller-free routine so you can *watch* the robot drive in
simulation: enable Autonomous in the sim GUI (or a dashboard) and it runs on its
own. It drives forward, strafes left, spins in place, then stops — a visible path
on the Field2d widget. Replace with real trajectory-following autos later.
"""

import math

import commands2

from subsystems.drivetrain import Drivetrain

# How long to hold each segment, and the demo speeds (well under the max).
_SEGMENT_S = 2.0
_SPEED_MPS = 1.0
_TURN_RPS = math.pi / 2


def demo_auto(drivetrain: Drivetrain) -> commands2.Command:
    """Forward, then strafe left, then spin, then stop — robot-relative."""

    def segment(vx: float, vy: float, omega: float) -> commands2.Command:
        return commands2.cmd.run(
            lambda: drivetrain.drive(vx, vy, omega, field_relative=False),
            drivetrain,
        ).withTimeout(_SEGMENT_S)

    stop = commands2.cmd.runOnce(
        lambda: drivetrain.drive(0.0, 0.0, 0.0, field_relative=False), drivetrain
    )

    return (
        segment(_SPEED_MPS, 0.0, 0.0)
        .andThen(segment(0.0, _SPEED_MPS, 0.0))
        .andThen(segment(0.0, 0.0, _TURN_RPS))
        .andThen(stop)
    )
