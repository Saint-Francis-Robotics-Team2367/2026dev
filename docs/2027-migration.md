# 2027 / SystemCore notes

2027 is the biggest FRC control-system change since the cRIO. This page records what changed
and how it shaped this codebase. RobotPy 2027 is **alpha** (`2027.0.0a7`) during the preseason,
so treat specifics as moving targets and verify against the installed package stubs
(`.venv/Lib/site-packages/**/*.pyi`) rather than older docs.

## SystemCore replaces the roboRIO

- New control system (**SystemCore**) and a new multi-platform **Driver Station**.
- NetworkTables is **NT4-only** (v3 removed; `pynetworktables` → `pyntcore`).
- Many legacy hardware APIs were **removed**: relay, analog output, SPI + SPI IMUs, analog gyro,
  DMA, built-in accelerometer, digital glitch filter, interrupts, counter, ultrasonic, analog
  trigger, Nidec Brushless, Servo, Jaguar.
- SystemCore adds multiple CAN buses, Smart IO, an **onboard IMU**, and an Expansion Hub.
- Robot-side Python is **3.14** (`linux_systemcore` wheels), matching our local interpreter.

## RobotPy / WPILib API changes that affected this code

**`wpimath` was flattened.** The `wpimath.kinematics` / `wpimath.geometry` /
`wpimath.controller` / `wpimath.trajectory` / `wpimath.system.plant` submodules are gone —
everything is top-level: `wpimath.SwerveDrive4Kinematics`, `wpimath.Translation2d`,
`wpimath.Rotation2d`, `wpimath.Pose2d`, `wpimath.PIDController`, `wpimath.DCMotor`, etc.

**Kinematics types were renamed:**

| Pre-2027 | 2027 |
|----------|------|
| `ChassisSpeeds` | `ChassisVelocities(vx, vy, omega)` |
| `SwerveModuleState` | `SwerveModuleVelocity(velocity, angle)` |
| `ChassisSpeeds.fromFieldRelativeSpeeds(...)` (static) | `ChassisVelocities(...).to_robot_relative(gyroAngle)` (instance) |
| `ChassisSpeeds.discretize(...)` (static) | `ChassisVelocities(...).discretize(dt)` (instance) |
| `kinematics.toSwerveModuleStates(...)` | `kinematics.to_swerve_module_velocities(...)` |
| `SwerveModuleState.optimize(...)` (in place) | `SwerveModuleVelocity.optimize(currentAngle)` (returns a new one) |

**Controllers were renamed** for the new Driver Station: `wpilib.XboxController` →
`wpilib.NiDsXboxController` (likewise PS4/PS5/Stadia), and `commands2.button.CommandXboxController`
→ `commands2.button.CommandNiDsXboxController`.

**Launching changed:** `wpilib.run(...)` is removed. The robot is launched by the `robotpy` CLI
(`robotpy sim` / `deploy` / `test`), or `wpilib.RobotBase.main(RobotClass)`.

**`pyfrc` is not in the default stack.** Simulation and tests come from `robotpy-cli` and
`wpilib.testing`, so there's no `physics.py`; we simulate via `simulation_periodic()` instead
(see [simulation.md](simulation.md)).

## Alpha 7 (`2027.0.0a7`) changes

**The whole RobotPy API is now snake_case** — methods, static constructors, and the robot /
subsystem lifecycle hooks. Pyright catches renamed *calls*, but **not renamed overrides**:
a `def autonomousInit` / `def simulationPeriodic` still type-checks and simply never runs.

| Alpha 6 | Alpha 7 |
|---------|---------|
| `autonomousInit` / `teleopInit` / `simulationPeriodic` (overrides) | `autonomous_init` / `teleop_init` / `simulation_periodic` |
| `toRobotRelative`, `toSwerveModuleVelocities`, `desaturateWheelVelocities`, `toChassisVelocities` | `to_robot_relative`, `to_swerve_module_velocities`, `desaturate_wheel_velocities`, `to_chassis_velocities` |
| `odometry.getPose()`, `rot.rotateBy()`, `Rotation2d.fromDegrees()` | `get_pose()`, `rotate_by()`, `from_degrees()` |
| `pose.X()` / `pose.Y()` | `pose.x` / `pose.y` (properties) |
| `wpimath.applyDeadband` | `wpimath.apply_deadband` |
| `NetworkTableInstance.getDefault()`, `getTable`, `get*Topic` | `get_default()`, `get_table`, `get_struct_topic` / … |
| commands2: `addRequirements`, `setDefaultCommand`, `withTimeout`, `andThen`, `cmd.runOnce` | `add_requirements`, `set_default_command`, `with_timeout`, `and_then`, `cmd.run_once` |
| controller `getLeftY()` etc. | `get_left_y()` etc. |

**SmartDashboard is removed** in favor of the Telemetry / Tunables APIs. `Field2d` is a
`TelemetryLoggable`: `telemetry.log("Field", field)` each loop publishes it at `/Telemetry/Field`
(was `SmartDashboard/Field`).

**A top-level `telemetry` module now ships with RobotPy** (`robotpy-telemetry`), which shadowed our
old `telemetry.py` — hence the rename to `drivetrain_telemetry.py`. Avoid top-level module names
that collide with RobotPy packages (`telemetry`, `tunables`, …).

Other a7 changes not yet touching our code: CAN device classes require a `CANPort` (Phoenix6
`CANBus(CANPort)` replaces `CANBus.systemcore(int)`), gamepad face buttons are directional
(`faceUp/Down/Left/Right`) with a default deadband, constants are ALL_CAPS, NT integer timestamps
are nanoseconds, and the `FMSInfo` table is now `DriverStation`.

## Platform support

- **Windows 11** (64-bit), **macOS 15+**, or **64-bit Linux with glibc ≥ 2.41** (Ubuntu 26.04 /
  Debian 13). The glibc floor is why the pyright CI job runs on Windows rather than the older
  `ubuntu-latest` — see [development.md](development.md#continuous-integration).
- On Windows, install the **Visual C++ 2022 redistributable (x64)** so the native wheels import.

## Living on alpha

- Install with `--pre` and keep versions pinned (`pyproject.toml`); bump as betas/RCs land.
- SystemCore Python vendordeps now exist as alphas (`phoenix6` 26.70.0a2, `robotpy-rev`
  2027.0.0a7.post1, both installable on 3.14 incl. `win_amd64`). The swerve modules use `phoenix6` (pinned in
  `pyproject.toml` `requires`; `robotpy sync` resolves a `linux_systemcore` wheel for the robot).
