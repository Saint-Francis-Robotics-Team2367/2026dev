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
   `SmartDashboard → Field` (drag it open), or use the **2D Field View** window. The robot icon
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
subsystem's `simulationPeriodic()`.

## How the robot moves in sim

1. Teleop calls `Drivetrain.drive()`, which runs inverse kinematics and sets each module's
   desired `SwerveModuleVelocity`.
2. `Drivetrain.simulationPeriodic()` (called by the scheduler only in simulation) advances the
   model one timestep: it integrates the robot **heading** from the last commanded rotational
   velocity and calls each module's `simulate(dt)` to accumulate wheel distance.
3. `Drivetrain.periodic()` feeds the heading + module positions into `SwerveDrive4Odometry`
   and publishes the resulting pose to **Field2d** — that's what you see move.

## Watch it drive in Autonomous

`commands/auto.py`'s `demo_auto` is a controller-free routine (drive forward → strafe → spin →
stop). `robot.py` schedules it in `autonomousInit`, so enabling **Autonomous** in the sim GUI makes
the robot drive itself on the field — the simplest way to *see* motion without a controller. It's a
placeholder for real trajectory-following autos.

> **2027 note:** `robotInit` was removed. Robot setup happens in the constructor
> (`def __init__(self): super().__init__(); ...`). Using `robotInit` silently does nothing.

## Dashboards (Elastic / AdvantageScope)

`telemetry.py` publishes the drivetrain state to NetworkTables as typed struct topics under the
`Drivetrain` table: `pose` (`Pose2d`), `chassisVelocities`, `moduleStates`
(`SwerveModuleVelocity[]`), plus `headingDegrees` and `speedMps`. `Field2d` is published under
`SmartDashboard/Field`. These use the WPILib struct schema, so any NT4 dashboard reads them — no
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
   `SmartDashboard/Field`).
4. Enable **Autonomous** in the sim GUI → the robot drives on the field, live.
5. Open a **Line Graph** tab → drag `Drivetrain/headingDegrees` / `speedMps` to plot.

### Elastic — driver dashboard

1. `robotpy sim`.
2. **Settings (gear) → IP Address Mode → `localhost`**.
3. **Add Widget** → `SmartDashboard/Field` for the field; add number/gauge widgets for
   `Drivetrain/headingDegrees` and `speedMps`.
4. Enable **Autonomous** in the sim GUI → widgets update live.

Note: both tools have a dedicated *swerve module* widget that expects the `SwerveModuleState[]`
struct; the 2027 rename to `SwerveModuleVelocity` means that specific widget may not parse it yet on
alpha. The pose/field view and all scalar values work regardless.

## Idealized modules

`SwerveModule` is a **kinematic** model: it's assumed to reach its commanded angle instantly
and its commanded wheel velocity exactly (`set_desired_state` sets angle/velocity directly;
`simulate` just integrates distance). That is deliberately simple and is enough to validate
kinematics, odometry, field-relative driving, and autonomous path logic.

It is **not** motor-fidelity: there's no acceleration limit, no steering lag, no battery sag.

## Extending it (when hardware/vendordeps arrive)

Keep the `SwerveModule` interface (`set_desired_state` / `get_state` / `get_position`) and
replace the internals with:

- real motor controllers (Phoenix6 / REVLib CAN) + closed-loop control (a `PIDController` for
  steering with continuous input, feedforward + PID for drive velocity), and
- a `wpilib.simulation` motor model — e.g. `DCMotorSim` fed by the module's output voltage — so
  the simulated encoders report realistic values back to the closed loop.

At that point the heading should come from the SystemCore onboard IMU (with an IMU sim) rather
than being integrated from the command.

## Tests

`tests/test_swerve.py` exercises this pipeline without the HAL/GUI: forward-command kinematics,
module distance integration, steering optimization, and a full 1-second odometry drive that
asserts the pose advances ~1 m. `tests/robot_test.py` boots the whole robot. Run both with
`robotpy test`.
