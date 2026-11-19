# Learning the Robot Code: Questions

Read the files in the order below and answer each question in your own words. Type your answer after "Your answer:" (replace the empty `>` line), and write the file name where you found it. Short answers are fine. Run `robotpy sim` once before you start so you can see the robot move.

## Part 1: The big picture (robot.py, robotcontainer.py)

**1.** Which file starts the robot code, and what is the name of the main robot class inside it?

**Your answer:**

> 

**2.** Find the functions in `robot.py` that end in `_init`, like `teleop_init`. When do you think each one runs?

**Your answer:**

> 

**3.** What is `RobotContainer` used for? Name two things it creates

**Your answer:**

> 

**4.** Where is the controller port number stored? Why keep numbers like that in one place instead of typing them everywhere?

**Your answer:**

> 

**5.** Which file has the drivetrain code, and which file has the numbers (like max speed)?

**Your answer:**

> 

**6.** Describe what happens from the moment the driver pushes a joystick to the moment the wheels spin. Name each file the action passes through

**Your answer:**

> 

## Part 2: Commands and subsystems (commands/, subsystems/)

**7.** What is a subsystem? Give one example from this repo

**Your answer:**

> 

**8.** What is a command? Give one example from this repo

**Your answer:**

> 

**9.** In your own words, how is a subsystem different from a command?

**Your answer:**

> 

**10.** What does `add_requirements(drivetrain)` do? What could go wrong without it?

**Your answer:**

> 

**11.** What is a default command? Which one does the drivetrain have?

**Your answer:**

> 

**12.** What happens to the robot when the driver holds the A button, then lets go?

**Your answer:**

> 

**13.** A command has `initialize`, `execute`, `is_finished`, and `end`. Pick one command and say what each one does

**Your answer:**

> 

**14.** Read `demo_auto` in `commands/auto.py`. List the steps the robot does, in order

**Your answer:**

> 

## Part 3: Object-oriented programming (all files)

**15.** What is a class? Pick one from the repo and say what it represents

**Your answer:**

> 

**16.** What is an object? How many `SwerveModule` objects get made, and where?

**Your answer:**

> 

**17.** What does `self` mean inside a class?

**Your answer:**

> 

**18.** Some variable names start with an underscore, like `self._drivetrain`. What do you think that tells other programmers?

**Your answer:**

> 

**19.** `Drivetrain` owns four `SwerveModule` objects. Why is that better than copying the module code four times?

**Your answer:**

> 

**20.** Why does `constants.py` exist? Name three constants and what they are for

**Your answer:**

> 

## Part 4: Swerve and simulation (subsystems/, docs/simulation.md)

**21.** What makes a swerve drive different from a tank drive?

**Your answer:**

> 

**22.** What is the difference between field-relative and robot-relative driving? Which one does the driver want in teleop?

**Your answer:**

> 

**23.** Each swerve module has three hardware devices. Name them and say what each one does

**Your answer:**

> 

**24.** What is simulation? Name two things you can test without a real robot

**Your answer:**

> 

**25.** What do `robotpy sim` and `robotpy test` each do?

**Your answer:**

> 

## Part 5: Short exercises

**26.** Draw a diagram with a box for each of these: `MyRobot`, `RobotContainer`, `Drivetrain`, `DriveByController`, `AlignToTag`, `SwerveModule`. Draw arrows to show which one creates, uses, or controls which. Label each arrow

**Your answer:** (attach a photo or drawing, or paste the file name here)

> 

**27.** Say how you would add a button so that pressing B resets the robot's position to the starting spot. Which file do you edit, and which existing function do you call? (Hint: look for `reset_pose`)

**Your answer:**

> 

**28.** Plan a new `Intake` subsystem with one motor. Which files would you create or change? What two functions would it need?

**Your answer:**

> 

**29.** A teammate says "the robot ignores my joysticks after I hold A once." Write down one guess for the cause and one thing you would check to test it

**Your answer:**

> 

**30.** Pick one number in `constants.py` marked as a placeholder. How would you find the real value on the robot?

**Your answer:**

>
