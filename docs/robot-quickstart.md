# Robot quickstart: deploy, switch CAN to classic, run from the Driver Station

Short path for putting the code on the robot (Pi 5 + CAN hat, community SystemCore image) and
spinning the motors. Background and troubleshooting: [pi5-canhat-bench.md](pi5-canhat-bench.md).

Assumes `ssh robot` works (host `robot.local`, user `systemcore`) and the devices are on 26.70.x
firmware. `HardwareIds.CAN_BUS` in `constants.py` must be `"can_s0"`.

## 1. Deploy (laptop)

```bash
rm -rf logs         # local sim .hoot logs would be uploaded otherwise
robotpy deploy      # uploads the code and restarts the robot program
```

## 2. Switch CAN to classic (robot, after every boot)

The image brings `can_s0` up as CAN FD, which goes bus-off and bounces. Switch it to classic
1 Mbps. It does not survive a reboot.

1. Upload `scripts/can_classic.sh` (SFTP: **Upload Folder** on `scripts/`; it lands in
   `/home/systemcore/guillaume/robot/scripts/`, the `remotePath` in `.vscode/sftp.json`).
2. Run it on the robot:
   ```bash
   ssh robot
   bash /home/systemcore/guillaume/robot/scripts/can_classic.sh   # stops watchdog, can_s0 -> classic
   ```
   The last line should be `OK: can_s0 is classic CAN, 1 Mbps`.
3. Restart the robot code so it picks up the bus:
   ```bash
   sudo systemctl restart robot.service
   ```

If the Driver Station shows "firmware version could not be retrieved", run
`ip -details link show can_s0`. `<FD,...> state BUS-OFF` means this step wasn't done.

## 3. Robot dashboard and logs (laptop)

The robot serves a web dashboard over HTTP, reachable from any browser on the same wired or Wi-Fi
network as the robot (try `http://robot.local`). It has a **Robot Program Log** card that streams
what the robot program prints. It reads "Waiting for output from the robot program..." until the
program prints something, so restart the robot code with the page open to see the startup lines.

Robot output is visible in three places:

| Where | How |
|---|---|
| Robot dashboard | **Robot Program Log** card, in the browser |
| Terminal | `ssh robot journalctl -u robot.service -f` (full history, includes tracebacks and Phoenix errors) |
| Driver Station console | Same `[robot]` / `[spin]` lines, sent through `dslog.log` (not yet confirmed on this DS) |

All our lines start with a tag: `[robot]` for lifecycle and Driver Station state, `[spin]` for the
motor test. Add your own with `from dslog import log` and `log("...")`; it prints to stdout and the
DS console, so it shows up everywhere above.

After a deploy or restart you should see `[robot] code started`, then `[robot] disabled`. The
`deploy-info` line in the journal shows which commit is running; check it is the one you just
deployed.

## 4. Driver Station

1. Open the 2027 Driver Station on the laptop and connect it to the robot (same network as
   `robot.local`).
2. Wait for `[robot] DS attached=True ...` in the log.
3. Select **Utility** (2027's name for Test mode) and **Enable**.
4. Stand clear. The motors spin one at a time (4 drive, then 4 steer), 2 s each at 1.5 V. The log
   shows `[spin] (n/8) ...` lines, then an `OK`/`FAIL` line per motor.
5. **Disable** when done. Leave Utility and re-enter it to rerun.

Teleop drives from a controller on port 0 and does not read the IMU yet. Don't use it on the
floor until the speed limits and module directions are checked.
