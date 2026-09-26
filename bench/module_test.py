"""Drive the robot code's own SwerveModule class on the real modules (robot LIFTED).

Builds the four modules exactly as ``Drivetrain`` does -- same class, same
``constants.py`` IDs / inversions / CANcoder offsets / gains -- and steps through a
short script of module states, printing commanded vs measured angle and speed. This
tests the real code path: device configs, steering through the CANcoder
(REMOTE_CANCODER), unit conversions, and the gains, on real motors.

What to watch (robot lifted, everyone clear):
  * Angle steps: all four wheels should end up parallel, pointing along the commanded
    direction (0 deg = robot forward, +90 deg = robot left). A wheel may sit 180 deg
    "backwards" -- that's ``optimize`` choosing the shorter turn; it's correct.
  * Rolling steps: all four treads should move the way the robot would drive for the
    commanded direction. A wrong one means that module's drive inversion is wrong.

Run from the bench venv (never the robot venv -- WPILib there switches Phoenix to
simulated devices):
    python bench/module_test.py
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root

from phoenix6 import unmanaged, utils  # noqa: E402
from wpimath import Rotation2d, SwerveModuleVelocity  # noqa: E402

from constants import HardwareIds  # noqa: E402
from subsystems.swervemodule import SwerveModule  # noqa: E402

_NAMES = ("FL", "FR", "BL", "BR")
_LOOP_S = 0.02
_ENABLE_TIMEOUT_S = 0.1
# (label, angle deg, speed m/s, seconds). Speeds stay slow: robot is lifted.
_STEPS = (
    ("point forward (0 deg)", 0.0, 0.0, 2.5),
    ("point left (+90 deg)", 90.0, 0.0, 2.5),
    ("point front-right (-45 deg)", -45.0, 0.0, 2.5),
    ("roll forward slowly", 0.0, 0.3, 3.0),
    ("roll left slowly", 90.0, 0.3, 3.0),
    ("stop, point forward", 0.0, 0.0, 2.0),
)


def _angle_error_deg(measured: float, target: float) -> float:
    """Error allowing the 180-deg flip that optimize() may choose."""
    err = (measured - target + 180.0) % 360.0 - 180.0
    return min(abs(err), abs(abs(err) - 180.0))


def _report(modules: list[SwerveModule], target_deg: float, speed: float) -> None:
    for name, module in zip(_NAMES, modules):
        state = module.get_state()
        deg = state.angle.degrees()
        # A flipped wheel reports the opposite speed sign; fold it back.
        flipped = abs((deg - target_deg + 180.0) % 360.0 - 180.0) > 90.0
        speed_along = -state.velocity if flipped else state.velocity
        print(
            f"    {name}: angle {deg:+7.1f} deg (err {_angle_error_deg(deg, target_deg):4.1f})"
            f"{' [flipped]' if flipped else '          '}"
            f"  speed {speed_along:+.3f} m/s (cmd {speed:+.2f})"
        )


def main() -> int:
    if utils.is_simulation():
        print("Phoenix is in SIMULATION mode -- run this from the bench venv.")
        return 1
    modules = [
        SwerveModule(
            name,
            HardwareIds.DRIVE_MOTOR_CAN[i],
            HardwareIds.TURN_MOTOR_CAN[i],
            HardwareIds.TURN_ENCODER_CAN[i],
            HardwareIds.TURN_ENCODER_OFFSETS_ROT[i],
            HardwareIds.CAN_BUS,
            HardwareIds.DRIVE_INVERTED[i],
        )
        for i, name in enumerate(_NAMES)
    ]
    print("modules configured. Starting positions:")
    _report(modules, 0.0, 0.0)

    try:
        for label, deg, speed, seconds in _STEPS:
            print(f"\n>>> {label}")
            desired = SwerveModuleVelocity(speed, Rotation2d(math.radians(deg)))
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                unmanaged.feed_enable(_ENABLE_TIMEOUT_S)
                for m in modules:
                    m.set_desired_state(desired)
                time.sleep(_LOOP_S)
            _report(modules, deg, speed)
    except KeyboardInterrupt:
        print("\ninterrupted")
    finally:
        # Command zero speed at the current angles, then cut the enable.
        for m in modules:
            m.set_desired_state(SwerveModuleVelocity(0.0, m.get_state().angle))
        unmanaged.feed_enable(0)
        print("\nstopped, actuators disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
