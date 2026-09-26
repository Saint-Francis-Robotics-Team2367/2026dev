"""Back up (or restore) every persistent config on the drivetrain's CTR devices.

Reads the full configuration from each TalonFX / CANcoder and writes a JSON file with,
per device: the serialized config, a readable dump (what ``--restore`` rebuilds from,
since ``deserialize`` is broken in phoenix6 26.3.0), and the settings that differ from
factory defaults. Close Phoenix Tuner X first.

    python bench/backup_configs.py                     # back up to bench/config_backup.json
    python bench/backup_configs.py --out other.json
    python bench/backup_configs.py --restore bench/config_backup.json   # write it back
"""

from __future__ import annotations

import argparse
import enum
import json
import math
import re
from datetime import datetime
from pathlib import Path

from phoenix6 import CANBus, configs, hardware, utils

_DEFAULT_OUT = Path(__file__).with_name("config_backup.json")
_TIMEOUT_S = 1.0


def _readable(cfg: object) -> list[str]:
    return [line.rstrip() for line in str(cfg).splitlines() if line.strip()]


def _same_value(a: str, b: str) -> bool:
    """Compare 'Name: value unit' lines, treating 16 and 16.0 (float noise) as equal."""
    if a == b:
        return True
    va, vb = a.split(":", 1)[-1].split(), b.split(":", 1)[-1].split()
    if not va or not vb or va[1:] != vb[1:]:
        return False
    try:
        return math.isclose(float(va[0]), float(vb[0]), rel_tol=1e-6, abs_tol=1e-9)
    except ValueError:
        return False


def _differences(cfg: object, default: object) -> list[str]:
    """Readable config lines that differ from factory defaults, keeping section headers."""
    out: list[str] = []
    section = ""
    default_lines = _readable(default)
    for i, line in enumerate(_readable(cfg)):
        if not line.startswith(" "):
            section = line.removeprefix("Config Group: ")
            continue
        if i >= len(default_lines) or not _same_value(line, default_lines[i]):
            out.append(f"{section.strip()}.{line.strip()}")
    return out


def _devices(bus: CANBus, talons: list[int], cancoders: list[int]):
    for i in talons:
        yield (
            f"talonfx_{i}",
            hardware.TalonFX(i, bus),
            configs.TalonFXConfiguration,
        )
    for i in cancoders:
        yield (
            f"cancoder_{i}",
            hardware.CANcoder(i, bus),
            configs.CANcoderConfiguration,
        )


def backup(args: argparse.Namespace) -> int:
    bus = CANBus(args.bus)
    result: dict = {
        "bus": args.bus,
        "saved": datetime.now().isoformat(timespec="seconds"),
        "devices": {},
    }
    failed = []
    for key, device, cfg_type in _devices(bus, args.talon, args.cancoder):
        cfg = cfg_type()
        status = device.configurator.refresh(cfg, _TIMEOUT_S)
        if not status.is_ok():
            failed.append(f"{key} ({status.name})")
            continue
        diffs = _differences(cfg, cfg_type())
        result["devices"][key] = {
            "serialized": cfg.serialize(),
            "non_default": diffs,
            "readable": _readable(cfg),
        }
        print(f"{key:12} saved, {len(diffs)} non-default setting(s)")
        for d in diffs:
            print(f"    {d}")

    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nwrote {args.out}")
    if failed:
        print(f"FAILED to read: {', '.join(failed)}")
        return 1
    return 0


def _attr(obj: object, readable_name: str) -> str:
    """Find the Python attribute for a readable config name ('PeakForwardDutyCycle' ->
    'peak_forward_duty_cycle', 'FeedbackRemoteSensorID' -> 'feedback_remote_sensor_id'),
    matching case- and underscore-insensitively."""
    key = readable_name.replace("_", "").lower()
    for name in dir(obj):
        if not name.startswith("_") and name.replace("_", "").lower() == key:
            return name
    raise AttributeError(f"{type(obj).__name__} has no config named {readable_name!r}")


def _parse_value(text: str, current: object) -> object:
    """Turn the readable 'value unit' text back into the attribute's own type."""
    token = text.split()[0]
    if isinstance(current, bool):
        return token == "True"
    if isinstance(current, enum.Enum):
        return type(current)[token.split(".", 1)[1]]
    if isinstance(current, (int, float)):
        # Some numeric defaults are ints (e.g. MagnetOffset = 0) even though the field
        # holds fractions, so only keep an int when the value really is whole.
        value = float(token)
        return int(value) if isinstance(current, int) and value.is_integer() else value
    # Phoenix enums are plain classes with int-backed values; look up by member name.
    member = token.split(".", 1)[-1]
    return getattr(type(current), member)


def _config_from_readable(cfg_type: type, lines: list[str]):
    """Rebuild a config object from the readable dump saved by ``backup``.

    Used instead of ``deserialize``: in phoenix6 26.3.0 it reports OK but zeroes
    every numeric field.
    """
    cfg = cfg_type()
    group = None
    for line in lines[1:]:  # first line is the class name
        if not line.startswith(" "):
            name = line.removeprefix("Config Group: ").strip()
            group = getattr(cfg, _attr(cfg, name))
            continue
        name, _, text = line.strip().partition(": ")
        attr = _attr(group, name)
        setattr(group, attr, _parse_value(text, getattr(group, attr)))
    return cfg


def _same_config(a: list[str], b: list[str]) -> bool:
    return len(a) == len(b) and all(_same_value(x, y) for x, y in zip(a, b))


def restore(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.restore).read_text(encoding="utf-8"))
    bus = CANBus(data["bus"])

    # Rebuild every config offline first and prove it reproduces the backup exactly,
    # before anything is written to a device.
    plan = []
    for key, entry in data["devices"].items():
        kind, _, num = key.partition("_")
        cfg_type = (
            configs.TalonFXConfiguration
            if kind == "talonfx"
            else configs.CANcoderConfiguration
        )
        cfg = _config_from_readable(cfg_type, entry["readable"])
        if not _same_config(_readable(cfg), entry["readable"]):
            bad = [
                f"{a} != {b}"
                for a, b in zip(_readable(cfg), entry["readable"])
                if not _same_value(a, b)
            ]
            print(f"{key}: rebuilt config does not match backup, nothing written:")
            print("\n".join(f"    {b}" for b in bad[:10]))
            return 1
        if isinstance(cfg, configs.CANcoderConfiguration):
            # The CANcoder stores the offset in 1/4096-rotation steps and drops a step
            # when the written value sits exactly on one; nudge a quarter step outward
            # so it lands on the intended step (bench-verified: exact read-back).
            offset = cfg.magnet_sensor.magnet_offset
            cfg.magnet_sensor.magnet_offset = offset + math.copysign(
                0.25 / 4096, offset
            )
        plan.append((key, kind, int(num), cfg))
    print(f"all {len(plan)} configs rebuilt and verified offline; writing...")

    failed = []
    for key, kind, num, cfg in plan:
        device = (
            hardware.TalonFX(num, bus)
            if kind == "talonfx"
            else hardware.CANcoder(num, bus)
        )
        status = device.configurator.apply(cfg, _TIMEOUT_S)
        # Read back and compare, rather than trusting the status code.
        check = type(cfg)()
        device.configurator.refresh(check, _TIMEOUT_S)
        ok = status.is_ok() and _same_config(
            _readable(check), data["devices"][key]["readable"]
        )
        print(f"{key:12} {'restored, verified' if ok else f'FAILED ({status.name})'}")
        if not ok:
            failed.append(key)
    return 1 if failed else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--bus", default="Drivetrain")
    p.add_argument("--talon", type=int, nargs="*", default=[1, 2, 4, 5, 7, 8, 10, 11])
    p.add_argument("--cancoder", type=int, nargs="*", default=[3, 6, 9, 12])
    p.add_argument("--out", default=str(_DEFAULT_OUT))
    p.add_argument("--restore", metavar="JSON", help="apply a backup file instead")
    args = p.parse_args()
    if utils.is_simulation():
        print(
            "Phoenix is in SIMULATION mode -- use the bench venv, not the robot venv."
        )
        return 1
    return restore(args) if args.restore else backup(args)


if __name__ == "__main__":
    raise SystemExit(main())
