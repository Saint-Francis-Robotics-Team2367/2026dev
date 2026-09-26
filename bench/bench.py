"""CTR CAN bench test: read (and optionally spin) TalonFX / CANcoder devices on a CANivore.

Runs on a laptop (Windows / macOS / Linux) or a Raspberry Pi -- no robot controller, no
WPILib. Outside FRC there is no Driver Station, so Phoenix only drives motors while this
script keeps feeding the enable signal (``unmanaged.feed_enable``); stop feeding and the
motors go neutral within ``_ENABLE_TIMEOUT_S``.

Read-only by default. Motors only move with an explicit ``--volts``, capped at
``_MAX_VOLTS``, for at most ``--seconds``. Ctrl+C stops them immediately.

Examples (from the bench venv, see README.md):
    python bench.py --talon 1 --cancoder 11                  # read only
    python bench.py --talon 1 --volts 1.5 --seconds 3        # spin at 1.5 V for 3 s
    python bench.py --bus can0 --talon 1                     # Linux SocketCAN adapter

Works with both phoenix6 26.3.x (2026 firmware) and 26.70.x (SystemCore alpha firmware):
devices are always given a ``CANBus`` object, which is all 26.70 accepts.

Run it from the *bench* venv, never the robot venv: when WPILib's HAL is importable, Phoenix
switches to simulated devices and prints plausible fake readings (12 V bus, 24 C). The script
refuses to run in that mode unless ``--allow-sim`` is given.
"""

from __future__ import annotations

import argparse
import time

from phoenix6 import (
    BaseStatusSignal,
    CANBus,
    controls,
    hardware,
    signals,
    unmanaged,
    utils,
)

# Safety limits. A bare module/motor on a bench needs very little voltage to move.
_MAX_VOLTS = 4.0
_MAX_SECONDS = 30.0
# How long motors stay enabled after the last feed. Short, so a hung script stops them.
_ENABLE_TIMEOUT_S = 0.1
_LOOP_PERIOD_S = 0.05  # 20 Hz: plenty for reading, well inside the enable timeout
_PRINT_PERIOD_S = 0.5


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "--bus",
        default="*",
        help='CANivore name/serial, "*" for any CANivore (default), or a SocketCAN '
        "interface such as can0 on Linux",
    )
    p.add_argument("--talon", type=int, action="append", default=[], help="TalonFX ID")
    p.add_argument(
        "--cancoder", type=int, action="append", default=[], help="CANcoder ID"
    )
    p.add_argument(
        "--volts",
        type=float,
        default=0.0,
        help=f"drive every TalonFX at this voltage (|V| <= {_MAX_VOLTS}); 0 = read only",
    )
    p.add_argument(
        "--seconds",
        type=float,
        default=5.0,
        help=f"how long to run (<= {_MAX_SECONDS})",
    )
    p.add_argument(
        "--allow-sim",
        action="store_true",
        help="run even if Phoenix is in simulation (readings are NOT real hardware)",
    )
    args = p.parse_args()
    if not args.talon and not args.cancoder:
        p.error("give at least one --talon or --cancoder ID")
    if abs(args.volts) > _MAX_VOLTS:
        p.error(f"--volts must be within +/-{_MAX_VOLTS}")
    if not 0 < args.seconds <= _MAX_SECONDS:
        p.error(f"--seconds must be in (0, {_MAX_SECONDS}]")
    return args


def _firmware(device: hardware.TalonFX | hardware.CANcoder) -> str:
    """Firmware as major.minor.bugfix.build, or '?' if the device didn't answer."""
    sig = device.get_version()
    sig.wait_for_update(0.5)
    if not sig.status.is_ok():
        return f"? ({sig.status.name})"
    v = int(sig.value)
    return f"{v >> 24 & 0xFF}.{v >> 16 & 0xFF}.{v >> 8 & 0xFF}.{v & 0xFF}"


def main() -> int:
    args = _parse_args()
    if utils.is_simulation():
        if not args.allow_sim:
            print(
                "Phoenix is in SIMULATION mode -- readings would be fake. This happens "
                "when WPILib is installed (e.g. the robot venv); use the bench venv. "
                "Pass --allow-sim to run anyway."
            )
            return 1
        print("*** SIMULATION: devices below are simulated, not real hardware ***")
    bus = CANBus(args.bus)
    talons = {i: hardware.TalonFX(i, bus) for i in args.talon}
    cancoders = {i: hardware.CANcoder(i, bus) for i in args.cancoder}

    print(f"bus {args.bus!r}: {bus.get_status().status.name}")
    time.sleep(0.25)  # let a little traffic arrive before judging the bus
    if bus.get_status().bus_utilization == 0.0:
        print(
            "  WARNING: no CAN traffic seen. If Phoenix Tuner X is open, close it (it "
            "holds the CANivore); otherwise check the bus name, power, and wiring."
        )
    for i, t in talons.items():
        print(f"  TalonFX  {i:>2}  firmware {_firmware(t)}")
    for i, c in cancoders.items():
        print(f"  CANcoder {i:>2}  firmware {_firmware(c)}")

    talon_signals = {
        i: (
            t.get_position(),
            t.get_velocity(),
            t.get_motor_voltage(),
            t.get_stator_current(),
            t.get_supply_voltage(),
            t.get_device_temp(),
        )
        for i, t in talons.items()
    }
    robot_enable = {i: t.get_robot_enable() for i, t in talons.items()}
    cancoder_signals = {i: c.get_absolute_position() for i, c in cancoders.items()}
    all_signals = [s for sigs in talon_signals.values() for s in sigs]
    all_signals += list(cancoder_signals.values())

    request = controls.VoltageOut(args.volts)
    neutral = controls.NeutralOut()
    if args.volts:
        print(
            f"\nSPINNING at {args.volts:+.2f} V for {args.seconds:.1f} s (Ctrl+C stops)"
        )
    else:
        print(f"\nread only for {args.seconds:.1f} s")

    end = time.monotonic() + args.seconds
    next_print = 0.0
    lock_checked = False
    try:
        while (now := time.monotonic()) < end:
            if args.volts:
                unmanaged.feed_enable(_ENABLE_TIMEOUT_S)
                for t in talons.values():
                    t.set_control(request)
            BaseStatusSignal.refresh_all(all_signals, report_error=False)

            # A device used on a roboRIO is "FRC-locked": it ignores feed_enable and
            # only enables from a Driver Station, so it just sits in brake.
            if args.volts and not lock_checked and now > end - args.seconds + 0.3:
                lock_checked = True
                BaseStatusSignal.refresh_all(
                    list(robot_enable.values()), report_error=False
                )
                locked = [
                    i
                    for i, sig in robot_enable.items()
                    if talons[i].is_connected
                    and sig.value != signals.RobotEnableValue.ENABLED
                ]
                if locked:
                    print(
                        f"  WARNING: TalonFX {locked} not enabled -- likely FRC-locked "
                        "(used on a roboRIO). Factory-default them in Phoenix Tuner X."
                    )

            if now >= next_print:
                next_print = now + _PRINT_PERIOD_S
                for i, (pos, vel, mv, amps, supply, temp) in talon_signals.items():
                    if not talons[i].is_connected:
                        print(f"TalonFX  {i:>2}  NOT CONNECTED")
                        continue
                    print(
                        f"TalonFX  {i:>2}  pos {pos.value:+9.3f} rot  "
                        f"vel {vel.value:+8.2f} rps  out {mv.value:+6.2f} V  "
                        f"{amps.value:6.2f} A  bus {supply.value:5.2f} V  "
                        f"{temp.value:4.1f} C"
                    )
                for i, abs_pos in cancoder_signals.items():
                    if not cancoders[i].is_connected:
                        print(f"CANcoder {i:>2}  NOT CONNECTED")
                        continue
                    print(f"CANcoder {i:>2}  abs {abs_pos.value:+.4f} rot")
            time.sleep(_LOOP_PERIOD_S)
    except KeyboardInterrupt:
        print("\ninterrupted")
    finally:
        # Stop explicitly rather than waiting out the enable timeout.
        for t in talons.values():
            t.set_control(neutral)
        unmanaged.feed_enable(0)
        print("motors neutral, actuators disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
