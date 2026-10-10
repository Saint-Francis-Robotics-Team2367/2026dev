#!/usr/bin/env bash
# Download aarch64 Linux wheels (SystemCore / Pi 5) from this machine for offline install.
#
# Usage: scripts/download_robot_packages.sh [requirements-file] [dest-dir]
#   env: PY_VERSION (default 3.13)  target Python version on the robot
#
# Why pip and not uv: some RobotPy wheels are tagged manylinux_2_41, and uv's
# --python-platform stops at manylinux_2_40. pip accepts any platform tag.
#
# Install on the target afterwards:
#   rsync -av wheels/ pi:~/wheels/
#   pip install --no-index --find-links ~/wheels -r requirements.txt

set -euo pipefail

cd "$(dirname "$0")/.."

REQUIREMENTS="${1:-requirements.txt}"
DEST="${2:-wheels}"
PY_VERSION="${PY_VERSION:-3.13}"

if [[ ! -f "$REQUIREMENTS" ]]; then
    echo "error: $REQUIREMENTS not found" >&2
    exit 1
fi

PLATFORMS=(
    manylinux_2_41_aarch64
    manylinux_2_40_aarch64
    manylinux_2_39_aarch64
    manylinux_2_28_aarch64
    manylinux_2_17_aarch64
    manylinux2014_aarch64
    linux_aarch64
)

platform_args=()
for p in "${PLATFORMS[@]}"; do
    platform_args+=(--platform "$p")
done

uvx pip download \
    -r "$REQUIREMENTS" \
    --dest "$DEST" \
    --pre \
    --only-binary=:all: \
    --implementation cp \
    --python-version "$PY_VERSION" \
    "${platform_args[@]}"

echo "Wheels saved to $DEST/ ($(find "$DEST" -name '*.whl' | wc -l | tr -d ' ') files)"
