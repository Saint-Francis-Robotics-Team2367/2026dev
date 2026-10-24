#!/usr/bin/env bash
# Switch a CAN interface from the image's CAN FD setup to classic CAN at 1 Mbps, for bench.py.
# Run this ON THE ROBOT (community SystemCore image), not on the laptop.
#
# Why: the image brings can_s0 up as CAN FD (1 Mbps / 2 Mbps). With that, bench.py loses the bus a few
# seconds after Phoenix starts (bus-off), and limelight_canbuswatchdog keeps bouncing the interface.
# Classic CAN at 1 Mbps works. See docs/pi5-canhat-bench.md.
#
# Usage: scripts/can_classic.sh [--keep-watchdog] [--restore] [interface]
#   interface        default can_s0
#   --keep-watchdog  do not stop limelight_canbuswatchdog (default: stop it first)
#   --restore        start the watchdog again; reboot to get the image's FD setup back
#
# Not persistent: a reboot restores the image's FD setup. Needs root (re-runs itself with sudo).

set -euo pipefail

WATCHDOG="limelight_canbuswatchdog.service"
IFACE="can_s0"
KEEP_WATCHDOG=0
RESTORE=0

for arg in "$@"; do
    case "$arg" in
        --keep-watchdog) KEEP_WATCHDOG=1 ;;
        --restore) RESTORE=1 ;;
        -h | --help)
            sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        -*)
            echo "error: unknown option $arg" >&2
            exit 1
            ;;
        *) IFACE="$arg" ;;
    esac
done

if [[ $EUID -ne 0 ]]; then
    exec sudo bash "$0" "$@"
fi

have_watchdog() {
    systemctl cat "$WATCHDOG" >/dev/null 2>&1
}

if ((RESTORE)); then
    if have_watchdog; then
        systemctl start "$WATCHDOG"
        echo "Started $WATCHDOG."
    fi
    echo "Reboot to restore the image's CAN FD setup on $IFACE."
    exit 0
fi

if ! ip link show "$IFACE" >/dev/null 2>&1; then
    echo "error: interface $IFACE not found (try: ip -br link | grep can_)" >&2
    exit 1
fi

if ((KEEP_WATCHDOG)); then
    echo "Leaving $WATCHDOG running."
elif have_watchdog; then
    systemctl stop "$WATCHDOG"
    echo "Stopped $WATCHDOG."
else
    echo "No $WATCHDOG on this system, skipping."
fi

ip link set "$IFACE" down
ip link set "$IFACE" up type can bitrate 1000000 fd off

details="$(ip -details link show "$IFACE")"
echo "$details"

if grep -q "<FD" <<<"$details"; then
    echo "WARNING: $IFACE still shows FD mode." >&2
    exit 1
fi
if ! grep -q "state UP" <<<"$details"; then
    echo "WARNING: $IFACE is not UP." >&2
    exit 1
fi
echo "OK: $IFACE is classic CAN, 1 Mbps. Run bench.py with --bus $IFACE."
