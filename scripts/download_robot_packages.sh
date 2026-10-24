#!/usr/bin/env bash
# Download robot packages on this machine, then install them on the robot and deploy.
#
# Steps:
#   1. pip download   aarch64 wheels into ./wheels for offline use (skip with --no-wheels)
#   2. robotpy installer download   robotpy + [tool.robotpy] requires from pyproject.toml into the cache
#   3. robotpy installer install    install those packages on the robot over SSH
#   4. robotpy deploy               upload code and run it (skip with --no-deploy)
#
# Bench mode (--bench): instead of the steps above, download the wheels in bench/requirements.txt
# into ./wheels-bench (no robotpy installer, no robot install/deploy). Pick the phoenix6 version
# by editing that file.
#
# Usage: scripts/download_robot_packages.sh [--no-wheels] [--no-deploy] [--bench]
#   env: ROBOT       robot hostname or IP        (default robot.local)
#        PY_VERSION  target Python for the wheels (default 3.13)
#        CACHE_ROOT  robotpy installer cache dir (default: robotpy's own, ~/wpilib/2027/robotpy)
#
# Why pip and not uv in step 1: some RobotPy wheels are tagged manylinux_2_41, and
# uv's --python-platform stops at manylinux_2_40. pip accepts any platform tag.

set -euo pipefail

cd "$(dirname "$0")/.."

ROBOT="${ROBOT:-robot.local}"
PY_VERSION="${PY_VERSION:-3.13}"
WHEELS_DIR="wheels"
DO_WHEELS=1
DO_DEPLOY=1
DO_BENCH=0

for arg in "$@"; do
    case "$arg" in
        --no-wheels) DO_WHEELS=0 ;;
        --no-deploy) DO_DEPLOY=0 ;;
        --bench) DO_BENCH=1 ;;
        -h | --help)
            sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "error: unknown argument $arg" >&2
            exit 1
            ;;
    esac
done

if [[ -x .venv/bin/python ]]; then
    PYTHON=.venv/bin/python
else
    PYTHON=python3
fi
ROBOTPY=("$PYTHON" -m robotpy)

# aarch64 platform tags for the robot (community SystemCore image: glibc 2.42, Python 3.13).
# Wheels are tagged with the glibc they were built on (phoenix6: 2_35, RobotPy: 2_39/2_41), so
# accept every minor from 2.17 up to the robot's 2.42.
platform_args=(--platform manylinux2014_aarch64 --platform linux_aarch64)
for minor in $(seq 17 42); do
    platform_args+=(--platform "manylinux_2_${minor}_aarch64")
done

if ((DO_BENCH)); then
    # Bench venv packages (phoenix6, no WPILib) come from bench/requirements.txt.
    BENCH_REQUIREMENTS="bench/requirements.txt"
    BENCH_DIR="wheels-bench"
    echo "==> Downloading $BENCH_REQUIREMENTS to $BENCH_DIR/ (aarch64, Python $PY_VERSION)"
    uvx pip download \
        -r "$BENCH_REQUIREMENTS" \
        --dest "$BENCH_DIR" \
        --pre \
        --only-binary=:all: \
        --implementation cp \
        --python-version "$PY_VERSION" \
        "${platform_args[@]}"
    echo "Wheels saved to $BENCH_DIR/ ($(find "$BENCH_DIR" -name '*.whl' | wc -l | tr -d ' ') files)."
    echo "Upload bench/ and $BENCH_DIR/ with SFTP, then on the robot:"
    echo "  python3 -m venv bench/.venv"
    echo "  bench/.venv/bin/pip install --no-index --find-links $BENCH_DIR -r $BENCH_REQUIREMENTS"
    exit 0
fi

cache_args=()
if [[ -n "${CACHE_ROOT:-}" ]]; then
    cache_args=(--cache-root "$CACHE_ROOT")
fi

# Robot-side packages come from pyproject.toml, not requirements.txt (that file has dev tools).
robot_packages=()
while IFS= read -r line; do
    robot_packages+=("$line")
done < <(
    "$PYTHON" -I - <<'EOF'
import tomllib

with open("pyproject.toml", "rb") as f:
    cfg = tomllib.load(f)["tool"]["robotpy"]

extras = ",".join(cfg.get("components", []))
extras = f"[{extras}]" if extras else ""
print(f"robotpy{extras}=={cfg['robotpy_version']}")
for req in cfg.get("requires", []):
    print(req)
EOF
)

echo "Robot packages: ${robot_packages[*]}"

if ((DO_WHEELS)); then
    echo "==> [1/4] Downloading aarch64 wheels to $WHEELS_DIR/"
    printf '%s\n' "${robot_packages[@]}" | uvx pip download \
        -r /dev/stdin \
        --dest "$WHEELS_DIR" \
        --pre \
        --only-binary=:all: \
        --implementation cp \
        --python-version "$PY_VERSION" \
        "${platform_args[@]}"
    echo "Wheels saved to $WHEELS_DIR/ ($(find "$WHEELS_DIR" -name '*.whl' | wc -l | tr -d ' ') files)"
fi

echo "==> [2/4] robotpy installer download"
"${ROBOTPY[@]}" installer download "${cache_args[@]}" --pre "${robot_packages[@]}"

echo "==> [3/4] robotpy installer install (robot: $ROBOT)"
"${ROBOTPY[@]}" installer install "${cache_args[@]}" --pre --robot "$ROBOT" "${robot_packages[@]}"

if ((DO_DEPLOY)); then
    echo "==> [4/4] robotpy deploy (robot: $ROBOT)"
    # Packages were just installed above, so skip deploy's own install step.
    "${ROBOTPY[@]}" deploy --robot "$ROBOT" --no-install
fi

echo "Done."
