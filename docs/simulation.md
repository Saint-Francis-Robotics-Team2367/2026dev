# Simulation

## Running the sim GUI

From the repo with the venv active:

```powershell
robotpy sim
```

(or `.\.venv\Scripts\python.exe -m robotpy sim` without activating). The **WPILib Simulation
GUI** window opens. Then:

1. **Watch autonomous — easiest, no controller.** In the **Robot State** panel, click
   **Autonomous**. `demo_auto` runs and the robot drives itself (forward → strafe → spin).
2. **See the field.** The published Field2d appears in the **NetworkTables** tree under
   `Telemetry → Field` (drag it open), or use the **2D Field View** window. The robot icon
   moves as it drives.
3. **Drive teleop with the keyboard.** Drag **Keyboard 0** from the *System Joysticks* list into
   *Joysticks* slot **0**, click **Teleoperated**, then use the keys shown in the Joysticks panel
   (left stick translates, right stick rotates).

Close the window to stop the sim. First launch may ask about keyboard/joystick settings — that's
normal.

> **Headless note:** the GUI needs a desktop, so it can't run in CI. Automated checks use
> `robotpy test` instead (see [below](#tests)).

## Why there's no `physics.py`

Older RobotPy projects modeled physics in a `physics.py` `PhysicsEngine` provided by
**`pyfrc`**. `pyfrc` is **not** part of the RobotPy 2027 stack — `robotpy sim` and
`robotpy test` now come from `robotpy-cli` and `wpilib.testing`. So this project uses
WPILib's current **device-simulation** pattern instead: the simulation logic lives in the
subsystem's `simulation_periodic()`.

## How the robot moves in sim

1. Teleop calls `Drivetrain.drive()`, which runs inverse kinematics and sets each module's
   desired `SwerveModuleVelocity`.
2. `Drivetrain.simulation_periodic()` (called by the scheduler only in simulation) advances the
   model one timestep: each module's `simulate(dt)` advances its motor physics, then the robot
   **heading** is integrated from the rotation rate the modules actually produce.
3. `Drivetrain.periodic()` feeds the heading + module positions into `SwerveDrive4Odometry`
   and publishes the resulting pose to **Field2d** — that's what you see move.

## Watch it drive in Autonomous

`commands/auto.py`'s `demo_auto` is a controller-free routine (drive forward → strafe → spin →
stop). `robot.py` schedules it in `autonomous_init`, so enabling **Autonomous** in the sim GUI makes
the robot drive itself on the field — the simplest way to *see* motion without a controller. It's a
placeholder for real trajectory-following autos.

> **2027 note:** `robotInit` was removed. Robot setup happens in the constructor
> (`def __init__(self): super().__init__(); ...`). Using `robotInit` silently does nothing.

## Dashboards (Elastic / AdvantageScope)

`drivetrain_telemetry.py` publishes the drivetrain state to NetworkTables as typed struct topics under the
`Drivetrain` table: `pose` (`Pose2d`), `chassisVelocities`, `moduleStates`
(`SwerveModuleVelocity[]`), plus `headingDegrees` and `speedMps`. `Field2d` is published under
`Telemetry/Field`. These use the WPILib struct schema, so any NT4 dashboard reads them — no
code changes needed.

**The sim GUI is still where you enable the robot / pick Autonomous.** The dashboards only
visualize the NetworkTables data. So the flow is always: start `robotpy sim`, connect the
dashboard, then enable a mode in the sim GUI.

Both tools ship with the WPILib installer, or download them standalone
([AdvantageScope](https://github.com/Mechanical-Advantage/AdvantageScope/releases),
[Elastic](https://github.com/Gold872/elastic_dashboard/releases)).

### AdvantageScope — field + plots

1. `robotpy sim` (starts the NT server).
2. **File → Connect to Simulator** (localhost; no config for a local sim).
3. Open a **2D Field** tab → drag `Drivetrain/pose` onto the **Robot** slot (or use
   `Telemetry/Field`).
4. Enable **Autonomous** in the sim GUI → the robot drives on the field, live.
5. Open a **Line Graph** tab → drag `Drivetrain/headingDegrees` / `speedMps` to plot.

### Elastic — driver dashboard

1. `robotpy sim`.
2. **Settings (gear) → IP Address Mode → `localhost`**.
3. **Add Widget** → `Telemetry/Field` for the field; add number/gauge widgets for
   `Drivetrain/headingDegrees` and `speedMps`.
4. Enable **Autonomous** in the sim GUI → widgets update live.

Note: both tools have a dedicated *swerve module* widget that expects the `SwerveModuleState[]`
struct; the 2027 rename to `SwerveModuleVelocity` means that specific widget may not parse it yet on
alpha. The pose/field view and all scalar values work regardless.

## Phoenix 6 modules in simulation

`SwerveModule` drives real Phoenix 6 devices: a TalonFX for drive (`VelocityVoltage`, wheel
rotations), a TalonFX for steer (`PositionVoltage` with continuous wrap on a `REMOTE_CANCODER`,
module rotations), and a CANcoder. In simulation Phoenix simulates those devices itself,
including their firmware closed loops. `SwerveModule.simulate(dt)` supplies the physics: two
`DCMotorSim` models (Kraken X60, placeholder inertias in `constants.py`) are driven by each
Talon's output voltage, and the resulting rotor positions/velocities and CANcoder angle are
written back through the devices' `sim_state`. So the sim has real acceleration, steering lag,
and closed-loop tracking error, driven by the same gains the robot will use.

Two Phoenix sim behaviors to know:

- **Phoenix's simulated devices run on wall-clock time.** `robotpy sim` runs in real time, so
  it behaves. `robotpy test` fast-forwards (the harness steps 0.2 s at a time), so the device
  firmware lags. The boot tests still pass, but they don't show realistic motion. Module
  behavior is tested in real time instead (below).
- **Phoenix takes its enable from WPILib's Driver Station.** Motors only move while the (sim)
  DS is enabled. Don't use `phoenix6.unmanaged.feed_enable` alongside WPILib: it fights the DS
  and the motors cut out intermittently. It's only for non-WPILib programs like `bench/`.

Heading is still integrated in sim (no IMU model yet), but now from the rotation rate the
modules actually produce, not the commanded one. On hardware it should come from the SystemCore
onboard IMU.

## Tests

- `tests/test_swerve.py`: pure wpimath (kinematics, `optimize`, odometry), with no HAL and no
  Phoenix. It runs in milliseconds.
- `tests/test_swervemodule_sim.py`: the Phoenix-backed `SwerveModule` against Phoenix's
  simulated devices, **in real time** (~9 s total). It checks that the module reaches the
  commanded velocity and angle, takes the shortest steering path, integrates distance
  consistently, and handles the CANcoder magnet offset.
- `tests/robot_test.py`: generated full-robot boot tests.

Run everything with `robotpy test` (~30 s).
