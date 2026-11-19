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
`super().__init__()` first.) `autonomous_init` schedules the autonomous command and
`teleop_init` cancels it. There is no `wpilib.run(...)` in 2027 — the robot is launched by
the `robotpy` CLI (`robotpy sim` / `deploy` / `test`).

## Wiring — `robotcontainer.py`

`RobotContainer` is where the robot is assembled, kept separate from the robot lifecycle:

- constructs the subsystems (currently just `Drivetrain`) and the driver controller
  (`CommandNiDsXboxController`),
- sets the drivetrain's **default command** to `DriveByController` (so teleop drives by
  default), and
- `configure_bindings()` binds buttons to commands: holding **A** runs `AlignToTag`.

## Subsystems — `subsystems/`

- **`SwerveModule`** — one module. Public interface: `set_desired_state()`, `get_state()`,
  `get_position()`, and `simulate(dt)`. Internally it's two Phoenix 6 TalonFX (drive
  velocity loop, steer position loop on a CANcoder) with `DCMotorSim` physics in simulation; see
  [simulation.md](simulation.md).
- **`Drivetrain`** — owns the four modules, the `SwerveDrive4Kinematics`, the
  `SwerveDrive4PoseEstimator`, and the `Field2d` widget. `drive(vx, vy, omega, field_relative)`
  runs inverse kinematics and pushes desired states to the modules (field-relative uses the
  pose estimate's heading, not the raw gyro, so it stays correct after a reset or a QuestNav
  correction); `periodic()` updates
  the estimator from wheel odometry and publishes the pose to Field2d.
  `add_vision_measurement()` fuses absolute poses; `reset_pose()` snaps the estimate.
- **`QuestNavSubsystem`** — feeds a Meta Quest headset running
  [QuestNav](https://questnav.gg/) into the drivetrain estimator. Each loop it drains the
  headset's unread pose frames, converts headset pose → robot pose through
  `QuestNavConstants.ROBOT_TO_QUEST`, and calls `Drivetrain.add_vision_measurement()`
  (skipping frames where the headset lost tracking). AprilTag correction happens on the
  headset, so the robot just sees better poses. Status goes to `QuestNavStatus/*`.

## QuestNav client — `questnav/`

QuestNav only ships a Java vendor library, so `questnav/` is a small Python port of it:
`protocol.py` is a hand-written codec for its protobuf messages (no `protobuf` dependency;
checked against reference bytes in `tests/test_questnav.py`) and `client.py` is the
NetworkTables client (`get_all_unread_pose_frames()`, `set_pose()`, `command_periodic()`,
connection/tracking/battery status). 2027 ntcore timestamps are nanoseconds; the client
converts them to `Timer` seconds.

## Commands — `commands/`

- **`DriveByController`** — the default teleop command. Reads the driver's sticks each
  `execute()`, applies a deadband, scales to max speeds, and calls `Drivetrain.drive()`
  field-relative. It `addRequirements(drivetrain)` so it yields to any other command that
  needs the drivetrain.
  The stick math lives in `stick_velocities()` so other commands can fall back to it.
- **`AlignToTag`** (`commands/align.py`) — runs while **A** is held. Its target is fixed at
  construction: the `AlignConstants.TARGET_TAG_ID` tag from the `robotpy-fields` layout
  (`AlignConstants.FIELD`, 2026 REBUILT Welded for now), moved `STANDOFF_M` (1 m) out along
  the tag's normal and turned to face it. Each loop, P controllers on field x, y, and heading
  (continuous) drive the pose estimate to the target, with speed capped along the path. It only
  aligns while `QuestNavSubsystem.pose_trusted()` (a tracking headset on a real robot, always
  in simulation); otherwise the driver keeps the sticks (logged to the DS console). The target shows
  on Field2d as `Target`; `Align/aligning` and `Align/atTarget` go to telemetry. QuestNav
  never reports which tags it sees, so this needs no camera, but the headset must use the
  same field layout as `AlignConstants.FIELD`.
- **`demo_auto`** (`commands/auto.py`) — a controller-free autonomous routine (a sequential
  composition of timed `drive()` segments). `RobotContainer.get_autonomous_command()` returns
  it; `robot.py` schedules it in `autonomous_init`.

## Telemetry — `drivetrain_telemetry.py`

`DrivetrainTelemetry` owns the NetworkTables publishers (struct topics for pose / chassis
velocities / module states, plus heading and speed). `Drivetrain.periodic()` calls it every
loop so dashboards (Elastic, AdvantageScope, Glass) see live state — see
[simulation.md](simulation.md#dashboards-elastic--advantagescope).

## Constants — `constants.py`

Grouped placeholders: `DriveConstants` (geometry + kinematics + limits), `ModuleConstants`
(gear ratios / wheel size), `HardwareIds` (CAN IDs, unused until vendordeps exist), and
`QuestNavConstants`, `AlignConstants` (target field/tag, standoff, gains, caps), and
`OIConstants` (controller port + deadband). Units are WPILib-standard: meters, radians,
seconds.

## Data flow each loop (teleop)

1. `DriveByController.execute()` → `Drivetrain.drive(vx, vy, omega)`
2. `drive()` → field-relative `ChassisVelocities` → `to_robot_relative()` → `discretize()` →
   `KINEMATICS.to_swerve_module_velocities()` → `desaturate_wheel_velocities()` → each module's
   `set_desired_state()` (which `optimize()`s to the shortest steering path).
3. `Drivetrain.periodic()` → `estimator.update()` → `Field2d.setRobotPose()`.
4. `QuestNavSubsystem.periodic()` → unread headset frames → `Drivetrain.add_vision_measurement()`.

In simulation, `Drivetrain.simulation_periodic()` advances the model between steps — see
[simulation.md](simulation.md).
