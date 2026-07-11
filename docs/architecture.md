# Architecture

This project uses the WPILib **command-based** framework (`commands2`). The pieces:

```
robot.py  ──creates──▶  RobotContainer  ──owns──▶  Drivetrain (Subsystem)
                              │                          ▲
                              └──sets default command──▶ DriveByController (Command)
```

## Entry point — `robot.py`

`MyRobot` subclasses `commands2.TimedCommandRobot`. That base class runs the
`CommandScheduler` every loop for us, so the **constructor** does one thing: build the
`RobotContainer`. (`robotInit` was removed in 2027 — setup goes in `__init__`, calling
`super().__init__()` first.) `autonomousInit` schedules the autonomous command and
`teleopInit` cancels it. There is no `wpilib.run(...)` in 2027 — the robot is launched by
the `robotpy` CLI (`robotpy sim` / `deploy` / `test`).

## Wiring — `robotcontainer.py`

`RobotContainer` is where the robot is assembled, kept separate from the robot lifecycle:

- constructs the subsystems (currently just `Drivetrain`) and the driver controller
  (`CommandNiDsXboxController`),
- sets the drivetrain's **default command** to `DriveByController` (so teleop drives by
  default), and
- `configure_bindings()` is where button → command bindings go as they're added.

## Subsystems — `subsystems/`

- **`SwerveModule`** — one module. Public interface: `set_desired_state()`, `get_state()`,
  `get_position()`, and `simulate(dt)`. Internally it's an idealized model today; see
  [simulation.md](simulation.md).
- **`Drivetrain`** — owns the four modules, the `SwerveDrive4Kinematics`, the
  `SwerveDrive4Odometry`, and the `Field2d` widget. `drive(vx, vy, omega, field_relative)`
  runs inverse kinematics and pushes desired states to the modules; `periodic()` updates
  odometry and publishes the pose to Field2d.

## Commands — `commands/`

- **`DriveByController`** — the default teleop command. Reads the driver's sticks each
  `execute()`, applies a deadband, scales to max speeds, and calls `Drivetrain.drive()`
  field-relative. It `addRequirements(drivetrain)` so it yields to any other command that
  needs the drivetrain.
- **`demo_auto`** (`commands/auto.py`) — a controller-free autonomous routine (a sequential
  composition of timed `drive()` segments). `RobotContainer.get_autonomous_command()` returns
  it; `robot.py` schedules it in `autonomousInit`.

## Telemetry — `telemetry.py`

`DrivetrainTelemetry` owns the NetworkTables publishers (struct topics for pose / chassis
velocities / module states, plus heading and speed). `Drivetrain.periodic()` calls it every
loop so dashboards (Elastic, AdvantageScope, Glass) see live state — see
[simulation.md](simulation.md#dashboards-elastic--advantagescope).

## Constants — `constants.py`

Grouped placeholders: `DriveConstants` (geometry + kinematics + limits), `ModuleConstants`
(gear ratios / wheel size), `HardwareIds` (CAN IDs, unused until vendordeps exist), and
`OIConstants` (controller port + deadband). Units are WPILib-standard: meters, radians,
seconds.

## Data flow each loop (teleop)

1. `DriveByController.execute()` → `Drivetrain.drive(vx, vy, omega)`
2. `drive()` → field-relative `ChassisVelocities` → `toRobotRelative()` → `discretize()` →
   `KINEMATICS.toSwerveModuleVelocities()` → `desaturateWheelVelocities()` → each module's
   `set_desired_state()` (which `optimize()`s to the shortest steering path).
3. `Drivetrain.periodic()` → `odometry.update()` → `Field2d.setRobotPose()`.

In simulation, `Drivetrain.simulationPeriodic()` advances the model between steps — see
[simulation.md](simulation.md).
