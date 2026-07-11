# 2027 / SystemCore notes

2027 is the biggest FRC control-system change since the cRIO. This page records what changed
and how it shaped this codebase. RobotPy 2027 is **alpha** (`2027.0.0a6`) during the preseason,
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
| `ChassisSpeeds.fromFieldRelativeSpeeds(...)` (static) | `ChassisVelocities(...).toRobotRelative(gyroAngle)` (instance) |
| `ChassisSpeeds.discretize(...)` (static) | `ChassisVelocities(...).discretize(dt)` (instance) |
| `kinematics.toSwerveModuleStates(...)` | `kinematics.toSwerveModuleVelocities(...)` |
| `SwerveModuleState.optimize(...)` (in place) | `SwerveModuleVelocity.optimize(currentAngle)` (returns a new one) |

**Controllers were renamed** for the new Driver Station: `wpilib.XboxController` →
`wpilib.NiDsXboxController` (likewise PS4/PS5/Stadia), and `commands2.button.CommandXboxController`
→ `commands2.button.CommandNiDsXboxController`.

**Launching changed:** `wpilib.run(...)` is removed. The robot is launched by the `robotpy` CLI
(`robotpy sim` / `deploy` / `test`), or `wpilib.RobotBase.main(RobotClass)`.

**`pyfrc` is not in the default stack.** Simulation and tests come from `robotpy-cli` and
`wpilib.testing`, so there's no `physics.py`; we simulate via `simulationPeriodic()` instead
(see [simulation.md](simulation.md)).

## Platform support

- **Windows 11** (64-bit), **macOS 15+**, or **64-bit Linux with glibc ≥ 2.41** (Ubuntu 26.04 /
  Debian 13). The glibc floor is why the pyright CI job runs on Windows rather than the older
  `ubuntu-latest` — see [development.md](development.md#continuous-integration).
- On Windows, install the **Visual C++ 2022 redistributable (x64)** so the native wheels import.

## Living on alpha

- Install with `--pre` and keep versions pinned (`pyproject.toml`); bump as betas/RCs land.
- Vendordeps (Phoenix6 / REVLib) for SystemCore aren't expected during alpha — hence the
  sim-primitive / idealized approach now, CAN motors later.
