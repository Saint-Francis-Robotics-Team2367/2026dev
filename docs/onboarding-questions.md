# Learning the Robot Code: Questions

Read the files in the order below and answer each question in your own words. Write down the file name where you found each answer. Short answers are fine. Run `robotpy sim` once before you start so you can see the robot move.

## Part 1: The big picture (robot.py, robotcontainer.py)

1. Which file starts the robot code, and what is the name of the main robot class inside it?
2. Find the functions in `robot.py` that end in `_init`, like `teleop_init`. When do you think each one runs?
3. What is `RobotContainer` used for? Name two things it creates
4. Where is the controller port number stored? Why keep numbers like that in one place instead of typing them everywhere?
5. Which file has the drivetrain code, and which file has the numbers (like max speed)?
6. Describe what happens from the moment the driver pushes a joystick to the moment the wheels spin. Name each file the action passes through

## Part 2: Commands and subsystems (commands/, subsystems/)

7. What is a subsystem? Give one example from this repo
8. What is a command? Give one example from this repo
9. In your own words, how is a subsystem different from a command?
10. What does `add_requirements(drivetrain)` do? What could go wrong without it?
11. What is a default command? Which one does the drivetrain have?
12. What happens to the robot when the driver holds the A button, then lets go?
13. A command has `initialize`, `execute`, `is_finished`, and `end`. Pick one command and say what each one does
14. Read `demo_auto` in `commands/auto.py`. List the steps the robot does, in order

## Part 3: Object-oriented programming (all files)

15. What is a class? Pick one from the repo and say what it represents
16. What is an object? How many `SwerveModule` objects get made, and where?
17. What does `self` mean inside a class?
18. Some variable names start with an underscore, like `self._drivetrain`. What do you think that tells other programmers?
19. `Drivetrain` owns four `SwerveModule` objects. Why is that better than copying the module code four times?
20. Why does `constants.py` exist? Name three constants and what they are for

## Part 4: Swerve and simulation (subsystems/, docs/simulation.md)

21. What makes a swerve drive different from a tank drive?
22. What is the difference between field-relative and robot-relative driving? Which one does the driver want in teleop?
23. Each swerve module has three hardware devices. Name them and say what each one does
24. What is simulation? Name two things you can test without a real robot
25. What do `robotpy sim` and `robotpy test` each do?

## Part 5: Short exercises

26. Draw a diagram with a box for each of these: `MyRobot`, `RobotContainer`, `Drivetrain`, `DriveByController`, `AlignToTag`, `SwerveModule`. Draw arrows to show which one creates, uses, or controls which. Label each arrow
27. Say how you would add a button so that pressing B resets the robot's position to the starting spot. Which file do you edit, and which existing function do you call? (Hint: look for `reset_pose`)
28. Plan a new `Intake` subsystem with one motor. Which files would you create or change? What two functions would it need?
29. A teammate says "the robot ignores my joysticks after I hold A once." Write down one guess for the cause and one thing you would check to test it
30. Pick one number in `constants.py` marked as a placeholder. How would you find the real value on the robot?

## Mentor answer key

- Q1: `robot.py`, class `MyRobot`
- Q3: it creates the subsystems, the controller, and the button bindings
- Q6: controller, then `DriveByController` in `commands/drive.py`, then `Drivetrain.drive()`, then each `SwerveModule`
- Q9: a subsystem is a piece of hardware and its functions, and a command is an action that uses subsystems
- Q10: it tells the scheduler which subsystem the command uses, so two commands can't drive the same motors at once
- Q11: a command that runs whenever nothing else is using the subsystem, here `DriveByController`
- Q12: `AlignToTag` takes over the drivetrain while A is held, and on release it stops and the stick driving resumes
- Q14: forward 2 seconds, strafe left 2 seconds, spin 2 seconds, stop
- Q16: four, created in a loop in `Drivetrain.__init__`
- Q18: it means "private, don't touch this from outside the class"
- Q19: the code is written once and reused, and each module only differs by the numbers passed in
- Q21: every wheel can point in any direction on its own, so the robot can move sideways and spin while moving
- Q22: field-relative means "forward" is toward the far end of the field no matter which way the robot faces, and it is what drivers want in teleop
- Q23: motor for driving, motor for steering, and a CANcoder that measures the steering angle
- Q25: `robotpy sim` opens the simulator window, and `robotpy test` runs the automatic tests with no window
- Q27: `robotcontainer.py`, bind `self.driver_controller.b()` to a command that calls `self.drivetrain.reset_pose(Pose2d())`
- Q29: possible guesses are that `AlignToTag` stays scheduled, or that the default command was never rescheduled, and the check is the log lines starting with `[align]`
