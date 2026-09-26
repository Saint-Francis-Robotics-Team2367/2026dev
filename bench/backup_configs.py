"""Back up (or restore) every persistent config on the drivetrain's CTR devices.

Reads the full configuration from each TalonFX / CANcoder and writes a JSON file with,
per device: the exact serialized config (restorable with ``--restore``), a readable
dump, and the settings that differ from factory defaults. Close Phoenix Tuner X first.

    python bench/backup_configs.py                     # back up to bench/config_backup.json
    python bench/backup_configs.py --out other.json
    python bench/backup_configs.py --restore bench/config_backup.json   # write it back
"""

from __future__ import annotations

import argparse
import json
import math
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


def restore(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.restore).read_text(encoding="utf-8"))
    bus = CANBus(data["bus"])
    failed = []
    for key, entry in data["devices"].items():
        kind, _, num = key.partition("_")
        if kind == "talonfx":
            device, cfg = (
                hardware.TalonFX(int(num), bus),
                configs.TalonFXConfiguration(),
            )
        else:
            device, cfg = (
                hardware.CANcoder(int(num), bus),
                configs.CANcoderConfiguration(),
            )
        cfg.deserialize(entry["serialized"])
        status = device.configurator.apply(cfg, _TIMEOUT_S)
        print(f"{key:12} {status.name}")
        if not status.is_ok():
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
