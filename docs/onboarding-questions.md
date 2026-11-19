# Onboarding Questions: Command-Based, OOP, and FRC Structure

Read the files in the order below. Answer each question in your own words, and cite the file and line you used. Run `robotpy sim` once before Part 1 so you have seen the robot move.

Difficulty: (E) easy, recall from the code. (M) medium, requires connecting two files. (H) hard, requires reasoning about behavior.

## Part 1: The FRC structure (robot.py, robotcontainer.py)

1. (E) Which class does `MyRobot` inherit from, and what job does that parent class do for you every 20 ms?
2. (E) List every robot mode hook in `robot.py` (names ending in `_init`). When does the robot framework call each one?
3. (M) Why does `RobotContainer` exist as a separate class instead of putting everything in `MyRobot`? Name two things that live in it.
4. (M) `MyRobot.__init__` builds the container. In the old WPILib API this happened in `robotInit`. What happens in 2027 if you write `robotInit` anyway? Why is that failure hard to notice?
5. (E) Which hook schedules the autonomous command, and which hook cancels it? Why must it be cancelled?
6. (M) `robot_periodic` runs in every mode. What is it used for here, and why is it a bad place to put drive logic?
7. (E) Where in the repo do the Driver Station controller port and deadband live? Why are they not typed directly into `drive.py`?
8. (M) Trace what happens, step by step, from "driver enables Teleop" to "wheels turn." Name every file the call passes through.

## Part 2: Command-based fundamentals (commands/, subsystems/)

9. (E) What is a Subsystem? What is a Command? Describe the difference in one sentence each.
10. (M) `Drivetrain` extends `commands2.Subsystem`. Which of its methods does the scheduler call automatically, and which are called only by commands?
11. (E) What does `add_requirements(drivetrain)` do in `DriveByController`? What would go wrong if you removed it?
12. (M) Two commands both require the drivetrain: `DriveByController` and `AlignToTag`. Explain exactly what the scheduler does when the driver presses and holds A, then releases it.
13. (E) What is a default command, and where is the drivetrain's default command set?
14. (E) List the four lifecycle methods of a `Command`. Which ones does `AlignToTag` override, and which does `DriveByController` override?
15. (M) `DriveByController` never overrides `is_finished`. What does that mean for how long it runs, and how does it ever stop?
16. (M) `AlignToTag` also never finishes, yet it has an `at_target` method. Why does the author keep the command running after the robot reaches the target?
17. (M) In `end(self, interrupted)`, what does the `interrupted` flag tell you? Give one example from this repo of an interruption.
18. (M) `button.a().while_true(self.align_command)` is used instead of `on_true`. Explain what `while_true` does when A is released. What would `on_true` do instead?
19. (H) `demo_auto` in `commands/auto.py` builds a command from smaller ones. Rewrite the sequence in plain English. What do `and_then`, `with_timeout`, `run`, and `run_once` each do?
20. (H) `demo_auto` is a function that returns a command, while `DriveByController` is a class. When would you choose each style? What do you lose with the function style?
21. (H) The lambda inside `segment(...)` captures `vx`, `vy`, and `omega`. Why does each segment keep its own values instead of all using the last one?

## Part 3: Object-oriented programming (all files)

22. (E) Find three classes in the repo that hold state in instance variables (names starting with `self._`). For each, list two of those variables.
23. (M) Why do many attributes start with an underscore, such as `self._drivetrain`? What convention does it signal, and does Python enforce it?
24. (M) Pick one subsystem and explain its public interface (the methods other code is expected to call). What is hidden behind it?
25. (M) `Drivetrain` owns a list of four `SwerveModule` objects. Is this inheritance or composition? Why is composition the better fit here?
26. (M) `SwerveModule.__init__` takes seven arguments, and `Drivetrain` builds four modules in a list comprehension. What differs between the four modules? Where does the differing data come from?
27. (H) `SwerveModule` has `set_desired_state`, `get_state`, `get_position`, and `simulate`. If a teammate wrote a `SimulatedSwerveModule` with the same four methods, what in `Drivetrain` would need to change? What does that tell you about interfaces?
28. (M) `QuestNavSubsystem.__init__` accepts an optional `questnav` argument. Why would the author add that parameter? What does it make easier in tests?
29. (E) `constants.py` groups values into classes such as `DriveConstants` and `OIConstants`. What is the benefit over module-level variables? Where is a constant used in `swervemodule.py`?
30. (M) `_scaled` and `stick_velocities` are plain functions, not methods. Why are they not part of `DriveByController`? Who else uses `stick_velocities`?
31. (M) `Command` objects pass references to the same `Drivetrain` instance. Why does the code create exactly one `Drivetrain` and pass it around instead of letting each command create its own?
32. (H) `DrivetrainTelemetry` is its own class instead of code inside `Drivetrain.periodic`. List the design benefits. Why does the comment say publishers "must be retained"?
33. (H) Find one place where a `@property` is used. What does it expose, and why is it read-only?
34. (M) `SpinAllMotors` uses a `@dataclass`. What does the decorator generate for you, and why is `signals` declared with `field(default_factory=list)` instead of `= []`?

## Part 4: Swerve drive and the data flow (subsystems/drivetrain.py, constants.py)

35. (E) What coordinate frame does WPILib use? Which direction is +x, which is +y, and which way is positive rotation?
36. (M) `DriveConstants` lists module locations in the order FL, FR, BL, BR. Why must this order match the module list and the HardwareIds tuples everywhere?
37. (M) Walk through `Drivetrain.drive()` line by line. For each step (field-relative conversion, discretize, kinematics, desaturate, per-module set), say what problem it solves.
38. (M) What is the difference between field-relative and robot-relative driving? Which one does the driver want in teleop? Which one does `demo_auto` use, and why?
39. (H) In `drive()`, why does field-relative conversion use `self.get_pose().rotation()` instead of the raw gyro heading?
40. (M) What does `desaturate_wheel_velocities` do when the driver commands full forward speed and full rotation at once?
41. (M) In `SwerveModule.set_desired_state`, what do `optimize` and `cosine_scale` accomplish? Give a concrete angle example.
42. (E) `periodic()` and `simulation_periodic()` both exist on `Drivetrain`. What does each do? Which one runs on a real robot?
43. (H) Odometry fuses wheel positions with vision. What does `SwerveDrive4PoseEstimator` need to compute a pose each loop? What does `add_vision_measurement` do to the estimate?
44. (M) In `QuestNavSubsystem.periodic`, why does the code skip frames where `frame.is_tracking` is false?
45. (H) `robotcontainer.py` has a comment about registering the questnav subsystem after the drivetrain. Why does order matter? What would go wrong if it was reversed?

## Part 5: Hardware and simulation (subsystems/swervemodule.py, docs/simulation.md)

46. (E) Name the three CAN devices in each swerve module and say what each one does.
47. (M) Why does the module code convert between meters/radians and rotations? Where does the conversion happen?
48. (M) Where do closed-loop controls run, in Python or on the motor controllers? What does that mean for the 20 ms loop timing?
49. (M) What does "simulation-first" mean for this repo? List two things you can verify without a robot.
50. (H) `simulate()` feeds physics results back into the Phoenix devices. Explain the loop: motor voltage in, physics update, sensor values out. Why is that loop necessary?
51. (H) Why is the `from wpilib ...` import inside `_init_sim` instead of at the top of `swervemodule.py`? Read the module docstring before answering.
52. (M) What is a CAN ID, and what happens if two devices on the same bus share one? What range is valid?

## Part 6: Commands that use sensors (commands/align.py)

53. (M) `AlignToTag` runs three `PIDController`s. What does each one control? Why is there no I or D term?
54. (M) Why does `calculate` cap the combined speed with `math.hypot` instead of limiting vx and vy separately?
55. (M) `self._heading.enable_continuous_input(-math.pi, math.pi)` handles a wraparound. Give an example where it matters: robot at +179 degrees, target at -179 degrees.
56. (E) What does the constructor resolve at robot startup, and why is failing early better than failing in a match?
57. (H) When QuestNav is not tracking, `execute` falls back to `stick_velocities`. Why is this fallback safer than stopping the robot? What is the risk of stopping?
58. (H) `standoff_pose` places the robot 1 m in front of a tag and turns it around. Explain the `Transform2d(standoff_m, 0.0, Rotation2d(math.pi))`. Which direction does the tag's +x axis point?

## Part 7: Tools, tests, and process

59. (E) What do `robotpy sim`, `robotpy test`, `pyright`, and `black --check .` each do? Which two are required checks on pull requests?
60. (M) Open `tests/test_swerve.py`. Pick one test and explain what it asserts and why it does not need a robot or simulation GUI.
61. (M) Why does `tests/robot_test.py` need `robotpy test` instead of plain `pytest`?
62. (E) What is NetworkTables, and which tools in this repo can read the data `DrivetrainTelemetry` publishes?
63. (M) Why does the project require Python 3.14 and `pip install --pre`? What does "alpha" mean for how much you trust old tutorials?

## Part 8: Apply what you learned (short exercises)

64. (M) Draw a diagram with boxes for `MyRobot`, `RobotContainer`, `Drivetrain`, `QuestNavSubsystem`, `DriveByController`, `AlignToTag`, and `SwerveModule`. Use arrows for "creates," "requires," and "calls."
65. (M) Add a button that resets the drivetrain pose to `Pose2d()` when you press B. Which file do you edit, and which existing method do you call?
66. (H) Design a new `Intake` subsystem with one motor, two public methods (`run`, `stop`), and a command that runs it while a trigger is held. List the files you would create or change.
67. (H) A teammate reports "the robot ignores my sticks after I hold A once." Name two hypotheses and the log line or telemetry topic that would confirm each.
68. (H) Pick one constant in `constants.py` that is a placeholder. Describe how you would measure or tune the real value.

## Mentor answer key (short)

- Q1: `TimedCommandRobot`, runs `CommandScheduler.run()` each loop
- Q4: it silently never runs, so `self.container` is missing and `autonomous_init` raises `AttributeError`
- Q11: the scheduler uses requirements to ensure one command per subsystem, and without them two commands drive the motors at once
- Q12: pressing A interrupts the default command, `AlignToTag` runs, and releasing A cancels it and the default resumes
- Q15: runs until interrupted, and the scheduler interrupts it when another command requires the drivetrain
- Q18: `while_true` schedules on press and cancels on release, while `on_true` schedules on press and lets the command run to its own end
- Q19: forward 2 s, then strafe left 2 s, then spin 2 s, then stop
- Q21: each call to `segment` creates a new scope, so the lambda closes over that call's arguments
- Q25: composition ("has a"), since modules are parts of the drivetrain and not a kind of drivetrain
- Q27: nothing, because `Drivetrain` only calls the interface, which is duck typing
- Q37: field-relative to robot-relative, discretize for skew, inverse kinematics, desaturate to the speed limit, then set each module
- Q39: the estimate is the field frame, and QuestNav corrections shift it away from the raw gyro
- Q41: `optimize` reverses the wheel instead of turning more than 90 degrees, and `cosine_scale` slows the wheel while it is misaligned
- Q45: odometry must update first so vision corrects the fresh estimate, and reversed order corrects a stale one
- Q51: importing WPILib makes Phoenix switch to simulated devices, which breaks the bench tool on real hardware
- Q55: the shortest turn is 2 degrees, but without continuous input the controller sees a 358 degree error and spins the long way
- Q57: stopping would trap the driver in a held-button command with no control, while sticks keep the robot controllable
- Q58: the tag's +x points out of its face, so moving along it by 1 m then rotating 180 degrees puts the robot's front toward the tag
