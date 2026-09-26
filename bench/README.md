# CAN bench test (CTR devices over CANivore)

Spin and read real TalonFX / CANcoder hardware **before SystemCore arrives**: laptop + CANivore
(or a Raspberry Pi with a CANivore or SocketCAN adapter). This is **not robot code**. It uses
Phoenix 6's non-FRC mode directly, with no WPILib and no Driver Station. What it's for: checking
CAN IDs, firmware, motor inversion, encoder direction, and CANcoder steer offsets, then recording
the results in `constants.py`.

## Setup (once)

Use a **separate venv**, never the robot `.venv`. When WPILib is importable, Phoenix switches to
simulated devices and prints fake readings (`bench.py` refuses to run in that mode).

```powershell
py -3.14 -m venv bench\.venv
& bench\.venv\Scripts\python.exe -m pip install -r bench\requirements.txt
```

On Linux / Raspberry Pi (64-bit OS), install CTR's `canivore-usb` kernel module from their APT
repository for the CANivore, or bring up a generic SocketCAN adapter at 1 Mbps. See
[Installing Phoenix 6 (non-FRC)](https://pro.docs.ctr-electronics.com/en/latest/docs/installation/installation-nonfrc.html).

### Which phoenix6 version (must match device firmware)

| `requirements.txt` | Device firmware | Notes |
|---|---|---|
| `phoenix6==26.3.0` (default) | 2026 (26.x) | No reflash; devices stay usable on a roboRIO. |
| `phoenix6==26.70.0a2` | 26.70.x (SystemCore alpha) | Reflash with Phoenix Tuner X first. Devices then no longer work with 2026 roboRIO code. |

The script prints each device's firmware on startup, so a mismatch shows up immediately.

The **robot code** pins `phoenix6==26.70.0a2` (`pyproject.toml`), so devices on the SystemCore
robot need 26.70.x firmware. Once you reflash for the robot, switch this file to 26.70.0a2 too.

### Before you run it

- **Close Phoenix Tuner X.** While it's open it holds the CANivore, and the script sees no traffic
  (every device shows `NOT CONNECTED`). Use one or the other.
- **Motors that have been on a roboRIO are "FRC-locked"**: they ignore the bench's enable and sit in
  brake. Factory-default them once in Tuner X (the script warns when it sees this). This wipes
  on-device configs; the robot code re-applies its own at startup. Plugging into a roboRIO re-locks
  them.

## Use

```powershell
# Read only (default): position, velocity, current, bus voltage, temp, CANcoder absolute angle
& bench\.venv\Scripts\python.exe bench\bench.py --talon 1 --cancoder 11

# Spin at 1.5 V for 3 s (|V| <= 4, <= 30 s). Ctrl+C stops immediately.
& bench\.venv\Scripts\python.exe bench\bench.py --talon 1 --volts 1.5 --seconds 3

# Specific CANivore by name, or a SocketCAN interface on Linux
& bench\.venv\Scripts\python.exe bench\bench.py --bus mycanivore --talon 1
python bench/bench.py --bus can0 --talon 1
```

Safety: motors only move with an explicit `--volts`. Phoenix's enable signal is fed every 50 ms
with a 100 ms timeout, so if the script hangs or dies, the motors go neutral on their own. On exit
the script commands neutral and disables actuators. Secure the motor or module before spinning it.

## Test the robot code on the real modules

`module_test.py` builds the four modules with the robot code's own `SwerveModule` class and the
values in `constants.py`, then steps through: point forward, point left, point front-right, roll
forward, roll left, and stop (about 16 s). It prints commanded vs. measured angle and speed for
each module. Robot lifted, everyone clear, Ctrl+C to stop:

```powershell
& bench\.venv\Scripts\python.exe bench\module_test.py
```

Numbers only prove the code tracks its commands. **Watch the robot** to confirm the directions are
right: at 0° all wheels point along the robot's length, at +90° they point sideways, at −45° they
point at the front-right, and when rolling forward every tread pushes the robot forward. A wheel
shown as `[flipped]` is fine: it turned 180° less and spins backwards instead.

## Back up / restore device settings

`backup_configs.py` saves every setting from all drivetrain Talons and CANcoders to
`config_backup.json` (restorable exactly), and lists what differs from factory defaults. Run it
before factory-defaulting anything.

```powershell
& bench\.venv\Scripts\python.exe bench\backup_configs.py
& bench\.venv\Scripts\python.exe bench\backup_configs.py --restore bench\config_backup.json
```

## Swerve module bring-up checklist

1. **IDs and firmware**: every device answers and reports the expected firmware.
2. **Drive direction**: `--volts +1` should drive the wheel forward. If not, note the inversion.
3. **Steer direction**: `--volts +1` on the steer motor should turn the module CCW (seen from above),
   and the CANcoder's `abs` should increase. If not, note the inversion or sensor direction.
4. **Steer offset**: point the wheel straight forward by hand and read the CANcoder `abs`. That's the
   module's magnet offset.
5. Record all of this in `constants.py` for the Phoenix6 swap in `subsystems/swervemodule.py`.
