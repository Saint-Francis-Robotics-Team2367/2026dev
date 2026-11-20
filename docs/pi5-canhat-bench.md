# Raspberry Pi 5 + MCP2518FD CAN hat on community SystemCore: bench bring-up

Goal: a demo that exercises every drivetrain motor in sequence, to prove the basics (wiring, IDs,
firmware, direction) before relying on SystemCore. The robot is a Pi 5 with a MCP2518FD CAN hat
running the **community SystemCore image**.

Status: the devices are now on **26.70.x firmware** and the robot code (`phoenix6==26.70.0a2`)
spins a TalonFX (ID 2) through the Driver Station in Utility mode (see "Spin the motors from robot
code"). That only works after `can_s0` is switched from the image's CAN FD setup to classic CAN
(step 4); in FD mode the bus bounces and Phoenix reports "firmware version could not be retrieved".
The earlier bench runs (`bench/bench.py`, `phoenix6==26.3.0`) were on 2026 firmware. The all-8-motor
Utility-mode run is written but not yet confirmed on the robot.

## Background

- **Official SystemCore** is a Limelight-built controller on a Raspberry Pi **Compute Module 5**. It
  has five CAN FD buses (`can_s0` to `can_s4`), each an **MCP2518FD on SPI** at 1 Mbps (40 MHz
  oscillators, `txqueuelen=1000`). Phoenix 6 reaches them over SocketCAN.
  ([teardown](https://dunkirk.sh/blog/frc-systemcore-image/))
- **Community image:** [netarcx/systemcore-rpi5-guide](https://github.com/netarcx/systemcore-rpi5-guide)
  patches the upstream CM5 image to boot on a Pi 5B. It was tested against Beta 10 and WPILib 2027
  Alpha 2 (older than this repo's `2027.0.0a7` / `phoenix6==26.70.0a2` pins).
  - Supports **USB-CAN adapters** (candleLight, PEAK, EMS), named `can_s0`+. Missing buses are filled
    with `vcan` placeholders so `robot.service` (which waits up to 15 s for all five) doesn't abort.
  - The guide says it **disables the SPI CAN overlays** (`sc-mcp2518-can*-spi*`) and that
    MCP2515/MCP2518 hats are unsupported. On this robot the SPI controllers are present anyway (see
    below), so the overlays are enabled on the image in use.
  - Needs an **RP2350 Pico** for carrier-board functions (RP2040 does not work). Expect cosmetic
    fault flags (brownout, IMU, CAN, ...); reset them from the dashboard.
- **CAN watchdog:** `limelight_canbuswatchdog.service` restarts a CAN interface (down, then up) when
  it sees a fault such as bus-off, with a cooldown of a couple of seconds. A drop-in
  (`limelight_canbuswatchdog.service.d/override.conf`) makes it watch only the first `can_s*`
  interface, i.e. `can_s0`. A restart of the interface right after a bus-off also produced
  `mcp251xfd ... CRC read error` / `Failed to set Requested Operation Mode` lines in `dmesg`.
- **Driver Station enable:** robot code gets its enable through `MrcCommDaemon` and the `can_heartbeat`
  kernel module, and Phoenix takes it from there. The standalone bench has no Driver Station; it feeds
  the enable signal itself, which worked with `phoenix6==26.3.0` on 2026 firmware on this image (see the version note in
  step 1).

## What this robot reports

Checked over SSH:

- Python 3.13, glibc 2.42. That covers the RobotPy a7 wheels (glibc >= 2.41) and the bench wheels.
- The image is minimal: no `ldd`, `getconf`, or `candump`. Use Python or `ip` instead.
- `ip -br link` lists `can_s0` and `can_s1` as `UP`, plus `can_s2`-`can_s4` and `can_d0`-`can_d19` as
  `UNKNOWN` (the `vcan` placeholders). There is no `can0`.
- `ip -details link show can_s0` / `can_s1` show real `mcp251xfd` controllers (`spi0.0` and `spi1.0`,
  40 MHz clock). The image configures them for **CAN FD**: 1 Mbps nominal, 2 Mbps data phase,
  sample point 0.875. With that setup the bench loses the bus a few seconds after Phoenix starts;
  switch to classic CAN first (step 4).
- With no CAN bus connected, both show `ERROR-PASSIVE (berr-counter tx 128)`. That is the normal state
  of a controller sending frames that nothing acknowledges. It is not a hat fault.
- Talons wired to the hat answer on `can_s0`. They were first seen on **2026 firmware** (TalonFX 2 on
  26.3.0.0, CANcoder 3 on 26.1.1.0) and have since been reflashed to **26.70.0.0** with Tuner X over a
  CANivore.

## Motors in this robot

From `constants.py` (`HardwareIds`; order FL, FR, BL, BR):

| | IDs |
|---|---|
| Drive TalonFX | 2, 8, 4, 10 |
| Steer TalonFX | 1, 7, 5, 11 |
| CANcoder | 3, 9, 6, 12 |

`CAN_BUS = "Drivetrain"` is a CANivore name. On SystemCore it must become `can_s0` (the hat's bus).
`scripts/*.py` default to `"CANivore"`; pass `can_s0` there too.

## Run `bench/bench.py` on the robot

The bench is not robot code. It runs in its own venv with **no WPILib**: when WPILib is importable,
Phoenix switches to simulated devices and `bench.py` refuses to run. So `robotpy sync` / `robotpy
deploy` are not the tools for it. Deploy would also start `robot.py` on the bus the bench needs.

The robot has no internet. Download on the laptop, upload with SFTP (`.vscode/sftp.json`, which
ignores `**/.venv`).

### 1. Download the bench packages (laptop)

The packages come from `bench/requirements.txt`: `phoenix6` and `robotpy-wpimath`, never full
`wpilib`. The `phoenix6` line must match the **device firmware**, and for this robot it is now
**`26.70.0a2`** (devices reflashed to 26.70.x):

- `26.70.0a2` (also the robot-code pin in `pyproject.toml`) reads the 26.70.x devices. It refuses to
  enable them outside robot code (`Cannot run the non-FIRST Phoenix 6 libraries on a FIRST
  Systemcore. Devices will remain disabled.`), so spin them from robot code instead.
- `26.3.0` matches 2026 firmware only. Against 26.70.x firmware it reports `This API version is too
  old for the firmware on the device`.

Then run the script. It needs only [uv](https://docs.astral.sh/uv/) (`brew install uv`) on the laptop,
no project venv:

```bash
scripts/download_robot_packages.sh --bench
```

This downloads aarch64 wheels for the robot's platform (Python 3.13 by default; override with
`PY_VERSION`) into `wheels-bench/`. Nothing is installed on the robot. If you change the `phoenix6`
line, delete `wheels-bench/` first so old wheels don't linger. Without `--bench` the same script
downloads, installs and deploys the robot-code packages from `pyproject.toml` (`[tool.robotpy]`); see
its header for the options.

### 2. Upload (SFTP)

Run **SFTP: Upload Folder** on `bench/` and `wheels-bench/`.

### 3. Wire the bus

- Connect the hat's CAN-H / CAN-L to the Talon chain (join grounds if the hat's docs say so).
- Terminate with 120 ohm at both ends: about 60 ohm across CAN-H/CAN-L with everything unpowered.
  Check whether the hat has its own termination jumper so the total isn't doubled.
- Power the Talons. The hat's bus is `can_s0`.

### 4. Check the CAN bus (robot)

Do this before touching Python, so a bus problem isn't mistaken for a software one. No packages needed.

```bash
sudo systemctl stop robot.service               # robot code holds the buses and sends frames
ip -br link | grep can_                         # can_s0 / can_s1 UP; the UNKNOWN ones are vcan
ip -details link show can_s0                    # real controller: mcp251xfd, bitrate 1000000
sudo dmesg | grep -i mcp251xfd                  # controllers registered, no probe errors
ip -s link show can_s0                          # run twice a few seconds apart, compare RX packets
```

If `ip` is missing, `ls /sys/class/net` lists the interface names.

What to expect on `can_s0`:

| State | Meaning |
|---|---|
| `ERROR-PASSIVE (berr-counter tx 128)`, RX stays 0 | Nothing is acknowledging frames: no device on the bus, Talons unpowered, or wiring fault. Normal with the bus unconnected. |
| `ERROR-ACTIVE`, berr-counters near 0, RX rising | Healthy. Powered devices are on the bus; go on. |
| `BUS-OFF` | Wiring or termination fault, or CAN-H/CAN-L swapped. Fix before continuing. |

An interface that shows `vcan` instead of `mcp251xfd` is a placeholder, not the hat.

#### Switch `can_s0` to classic CAN (every boot)

The image brings `can_s0` up as CAN FD (1 Mbps / 2 Mbps). With that, `bench.py` works for a few seconds
and then the interface goes bus-off, about when Phoenix finishes initializing (the log shows
`[phoenix-diagnostics] Server ... running` just before the devices turn `NOT CONNECTED`). Run
`bench.py` on classic CAN at 1 Mbps instead. Other FD settings were tried and fail the same way (FD on
with a 0.750 sample point; FD on with a 1 Mbps data phase), so FD itself is the problem, not the sample
point or the data rate. The cause is not known. `scripts/can_classic.sh` does it (SFTP uploads it with
the rest of `scripts/`; run it on the robot):

```bash
scripts/can_classic.sh            # can_s0 by default; pass another interface name to change it
```

It stops `limelight_canbuswatchdog.service`, takes the interface down, brings it up with
`type can bitrate 1000000 fd off`, prints `ip -details link show`, and exits non-zero if the
interface still shows FD or isn't UP. Expect `mtu 16`, no `FD` on the `can <...>` line, and
`ERROR-ACTIVE`. It re-runs itself with `sudo`. If the file lost its execute bit in the upload, run it
as `bash scripts/can_classic.sh`.

This is not persistent: a reboot restores the image's FD setup, and the watchdog service is enabled at
boot. It also affects anything else using `can_s0`, so do it only for bench sessions. To finish,
`scripts/can_classic.sh --restore` starts the watchdog again, then reboot to get FD back (whether
restarting the watchdog alone restores FD is untested).

The watchdog was stopped while this was verified. `--keep-watchdog` leaves it running, to test
whether it is harmless once the interface is classic; with it running, a fault during a run makes it
bounce the interface.

### 5. Create the venv (robot)

```bash
cd ~/guillaume/robot
python3 -m venv bench/.venv                     # no --system-site-packages
bench/.venv/bin/pip install --no-index --find-links wheels-bench -r bench/requirements.txt
bench/.venv/bin/python -c "import wpilib"       # must fail with ModuleNotFoundError
```

- If `python3 -m venv` fails with an `ensurepip` error, extract the wheels instead:
  `mkdir -p bench/libs; for w in wheels-bench/*.whl; do python3 -m zipfile -e "$w" bench/libs; done`,
  then run the bench with `PYTHONPATH=bench/libs python3 bench/bench.py ...`.
- `robotpy-wpimath` is only for `module_test.py`; `bench.py` doesn't need it. It is wpimath only, so
  the `import wpilib` check above still fails as it should.

### 6. Read, then spin

Always pass `--bus can_s0`. The default (`*`) means "any CANivore", and `can0` does not exist on this
image (`INVALID_NETWORK`, every device `NOT CONNECTED`).

```bash
sudo systemctl stop robot.service               # skip if already stopped in step 4

# read-only first: firmware, position, bus voltage
bench/.venv/bin/python bench/bench.py --bus can_s0 --talon 2 --cancoder 3

# one motor, low voltage, secured
bench/.venv/bin/python bench/bench.py --bus can_s0 --talon 2 --volts 1.5 --seconds 3

sudo systemctl start robot.service
```

The read-only run prints each device's firmware (here `26.3.0.0` and `26.1.1.0`), then live readings
(bus about 12.6 V). Two messages showed up in that run and are not a problem when devices answer:
`WARNING: no CAN traffic seen` and `CANbus Failed Bring-up: can_s0`. The spin test worked afterwards.

If `robot.service` is not found, check `systemctl list-units | grep -i robot`. With no devices
connected, a read-only run should start cleanly and report every device as `NOT CONNECTED`; that proves
the venv and Phoenix install.

Safety: motors only move with an explicit `--volts` (|V| <= 4, <= 30 s). The enable signal is fed every
50 ms with a 100 ms timeout, so a hung or dead script leaves motors neutral. Secure the motor or
module before spinning it.

## Troubleshooting

- **`INVALID_NETWORK` / every device `NOT CONNECTED` on the first try:** wrong `--bus`. Use `can_s0`.
- **Devices read fine for 3-5 s, then everything is zero / `NOT CONNECTED`, and `can_s0` keeps
  bouncing (`ip -t monitor link`, `CANbus Network Down` / `Up`):** `can_s0` is still in the image's CAN FD
  mode, goes bus-off, and the watchdog keeps restarting it. Switch to classic CAN (step 4).
  `dmesg` then shows `bus-off`, and after watchdog restarts, `mcp251xfd ... CRC read error`.
- **Devices show `NOT CONNECTED` with the right bus:** check termination, CAN-H/L not swapped, the
  Talons powered, and that `robot.service` is stopped.
- **`ERROR-PASSIVE` / `BUS-OFF`** (`ip -details link show can_s0`): with a bus connected, usually
  termination or wiring. With nothing connected it is expected (see above).
- **`Firmware Too Old`:** the venv's `phoenix6` is older than the devices' firmware (or newer than
  2026 firmware). Match `bench/requirements.txt` to the firmware (`26.70.0a2` for 26.70.x), delete
  `wheels-bench/`, re-download, and reinstall (steps 1, 2, 5).
- **`non-FIRST Phoenix 6 libraries on a FIRST Systemcore`:** expected for the bench on this image;
  it can read but not enable. Spin from robot code (below).
- **Driver Station alert "firmware version could not be retrieved" and `ip -details link show can_s0`
  shows `<FD,...> state BUS-OFF`:** the FD bounce. Run `scripts/can_classic.sh` (step 4), then
  restart robot code.
- **Motors sit in brake:** FRC-locked from a roboRIO. Factory-default once in Tuner X, but run
  `bench/backup_configs.py` first.

## Spin the motors from robot code (Utility mode)

Robot code gets its enable from the Driver Station, so this is how to spin motors once the devices
are on 26.70.x firmware. With `HardwareIds.CAN_BUS = "can_s0"` in `constants.py`:

1. On the robot, switch to classic CAN: `bash scripts/can_classic.sh`. It does not survive a reboot.
2. Deploy (`robotpy deploy`; `logs/*.hoot` from local sim runs get uploaded too, delete `logs/` first).
3. Watch the output: `ssh robot journalctl -u robot.service -f`, the Driver Station console, or the
   robot dashboard's Robot Program Log. Look for `[robot] code started`.
4. In the Driver Station select **Utility** (2027's name for Test mode) and enable.

`SpinAllMotors` (`commands/debug.py`) spins each drive motor and then each steer motor, one at a
time, at `DebugConstants.SPIN_VOLTS` for `SPIN_SECONDS`, logging `[spin] ...` once a second, then
prints an `OK`/`FAIL` summary line per motor. Every Driver Station state change is logged as
`[robot] DS attached=... enabled=... mode=... opmode=...`. Leave Utility and re-enter it to rerun.
Output goes through `dslog.log` (stdout plus `hal.send_console_line`).

## Suggested order

1. Done: read and spin Talon 2 / CANcoder 3 on `can_s0` with `bench.py` (2026 firmware), then with
   robot code in Utility mode (26.70.x firmware).
2. Run all 8 motors in sequence from robot code (Utility mode, `SpinAllMotors`) and record the
   `OK`/`FAIL` summary. Written, not yet confirmed on the robot.
3. Done: devices on 26.70.x firmware (flashed with Tuner X over a CANivore; flashing through the hat
   is still unverified).
4. Drive a module from robot code (Teleop), starting with a slow no-joystick test on blocks.

## Open questions

- Exact hat model, and what `can_s1` (a second real controller on `spi1.0`) is wired to.
- Whether the SPI overlays are enabled by the image itself or were added by hand, and where they are
  defined (needs inspection of the image or `/boot/firmware/config.txt` on the robot).
- Whether the bench needs the watchdog stopped once `can_s0` is classic (try
  `scripts/can_classic.sh --keep-watchdog`), and how to make classic mode survive a reboot for bench
  sessions (the image sets FD at boot; where is not yet found).
- Robot code (`phoenix6==26.70.0a2`) spins a motor on classic CAN at 1 Mbps, so it does not need
  the image's FD setup. Whether classic mode survives a long run with the full drivetrain is untested.
- `bench.py` prints `CANbus Failed Bring-up` even when it works: probably Phoenix failing to configure
  the interface as a non-root user. Not verified.
- Name of the robot-code service on this image (`robot.service` is taken from the teardown).
- How to flash 26.70.x firmware onto the Talons and CANcoders with this setup (Tuner X normally needs
  a CANivore, roboRIO or SystemCore connection).

## Sources

- [netarcx/systemcore-rpi5-guide](https://github.com/netarcx/systemcore-rpi5-guide)
- [Reverse engineering the FRC SystemCore image](https://dunkirk.sh/blog/frc-systemcore-image/)
- [Phoenix 6 requirements (CTR)](https://v6.docs.ctr-electronics.com/en/latest/docs/installation/requirements.html)
- [Chief Delphi: Systemcore raspberry pi?](https://www.chiefdelphi.com/t/systemcore-raspberry-pi/503847)
