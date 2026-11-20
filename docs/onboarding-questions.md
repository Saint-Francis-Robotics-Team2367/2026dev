# Learning the Robot Code: Questions

Read the files in the order below and answer each question in your own words. Type your answer after "Your answer:" (replace the empty `>` line), and write the file name where you found it. Short answers are fine. Run `robotpy sim` once before you start so you can see the robot move.

## Part 1: The big picture (robot.py, robotcontainer.py)

**1.** Which file starts the robot code, and what is the name of the main robot class inside it?

**Your answer:**

> robot.py, MyRobot

**2.** Find the functions in `robot.py` that end in `_init`, like `teleop_init`. When do you think each one runs?

**Your answer:**

__init__ -> starts when the code runs
__autonomousinit__ -> runs when the auton period starts
__teleopinit__ -> starts when the auton period ends
__disabledinit__ -> runs when the robot is disabled
__utilityinit__ -> runs when the robot is in utility mode, it would spin the motors one by one to check functionality

**3.** What is `RobotContainer` used for? Name two things it creates

**Your answer:**

> puts all the different parts of the robot together
drivetrain, questnav

**4.** Where is the controller port number stored? Why keep numbers like that in one place instead of typing them everywhere?

**Your answer:**

> In constants.py in the OIConstants class, and if we want to chqange it it will be 
easier to change if all of them are in one place

**5.** Which file has the drivetrain code, and which file has the numbers (like max speed)?

**Your answer:**

> 
drivetrain.py(in subsystems folder) and constants.py

**6.** Describe what happens from the moment the driver pushes a joystick to the moment the wheels spin. Name each file the action passes through

**Your answer:**

> when the driver pushes a joystick, it goes to robotcontainer.py. Then from there it goes to drive.py where the joystick input is read. From drive.py, it goes to drivetrain.py and that goes into swerve modules where it calculates the angle it needs to go.

## Part 2: Commands and subsystems (commands/, subsystems/)

**7.** What is a subsystem? Give one example from this repo

**Your answer:**

> a subsystem that performs a specific task but it has other things that goes along with it.

**8.** What is a command? Give one example from this repo

**Your answer:** 

> commands are files that get inputs for the robot that drives

**9.** In your own words, how is a subsystem different from a command?

**Your answer:**

> a subsystem is the part of the robot and has commands in it. Commands actually do the actions

**10.** What does `add_requirements(drivetrain)` do? What could go wrong without it?

**Your answer:**

> tells the scheduler that we need to use the drivetrain.
    prioritizes using the drivetrain over other commands

**11.** What is a default command? Which one does the drivetrain have?

**Your answer:**

> default command is a job that a subsystem does when it doesnt have anything to do
the default command for the drivetrain is to check for an input from the controller

**12.** What happens to the robot when the driver holds the A button, then lets go?

**Your answer:**

> it starts the align to tag command and starts the command. It drives to a spot 1 m in front of the april tag, aligns itself, then stops the wheels, and gives control back to the controller

**13.** A command has `initialize`, `execute`, `is_finished`, and `end`. Pick one command and say what each one does

**Your answer:**

> align to tag -> initalize resets all the steering values

execute -> will align if it can, if it cant align(if the robot doesnt know where it is) it will stop

is_finished -> no is_finished, automatically ends when a is released

end -> runs when u let go. Stops the robot and removes the target marking and logs it.

**14.** Read `demo_auto` in `commands/auto.py`. List the steps the robot does, in order

**Your answer:**
Forward at 1, then goes left at 1, then spins in place, then stops


> 

## Part 3: Object-oriented programming (all files)

**15.** What is a class? Pick one from the repo and say what it represents

**Your answer:**

> a class is a template for creating objects.
an example of a class is the questnavsubsystem, finds the location of the robot

**16.** What is an object? How many `SwerveModule` objects get made, and where?

**Your answer:**

> an object is one instance of a class. 4 swerve modules are created in the drivetrain subsystem

**17.** What does `self` mean inside a class?

**Your answer:**

> self refers to an instance of that class

**18.** Some variable names start with an underscore, like `self._drivetrain`. What do you think that tells other programmers?

**Your answer:**

> it tells other people that only the class should be using it and other classes should not touch this variable.
private variable

**19.** `Drivetrain` owns four `SwerveModule` objects. Why is that better than copying the module code four times?

**Your answer:**

> it allows more customization individually. if we want to make a change to one of them, it is easier.

**20.** Why does `constants.py` exist? Name three constants and what they are for

**Your answer:**

> each wheel and the elec could turn a different amount of times with the same value. To set them equal to each other we use constants.

front left location
front right location
back left location
back right location



## Part 4: Swerve and simulation (subsystems/, docs/simulation.md)

**21.** What makes a swerve drive different from a tank drive?

**Your answer:**

> tank drive cant go diagonally, it can go forwards and backwards and to turn one wheel has to move faster than the other
swerve drive can move freely, but each wheel has 2 motors

**22.** What is the difference between field-relative and robot-relative driving? Which one does the driver want in teleop?

**Your answer:**

> the driver wants field-relative because we are looking at it from a birdseye view and we are not moving with the robot.
field relative -> north south east and west
robot relative -> left and right

**23.** Each swerve module has three hardware devices. Name them and say what each one does

**Your answer:**

> encoder(tells us the angle at which the wheel is pointing)
- drive(the movement and it spins the wheel to the right speed)
- steer(points it in the right direction)

**24.** What is simulation? Name two things you can test without a real robot

**Your answer:**

> testing the code without using the actual robot(pretend environment and running the code).
- test auton
- test driving

**25.** What do `robotpy sim` and `robotpy test` each do?

**Your answer:**

> robotpy sim runs the simulation gui
robotpy test runs automated checks and gives us a pass or fail

## Part 5: Short exercises

**26.** Draw a diagram with a box for each of these: `MyRobot`, `RobotContainer`, `Drivetrain`, `DriveByController`, `AlignToTag`, `SwerveModule`. Draw arrows to show which one creates, uses, or controls which. Label each arrow

**Your answer:** (attach a photo or drawing, or paste the file name here)

> ![alt text](IMG_0222.HEIC)

**27.** Say how you would add a button so that pressing B resets the robot's position to the starting spot. Which file do you edit, and which existing function do you call? (Hint: look for `reset_pose`)

**Your answer:**

> robotcontainer.py and call drivetrain.resetpose

**28.** Plan a new `Intake` subsystem with one motor. Which files would you create or change? What two functions would it need?

**Your answer:**

> i would create an intake subsystem file and it would need a function to spin the motor and a function to get inputs. Add the can id and the speed we want it to go at into constants

**29.** A teammate says "the robot ignores my joysticks after I hold A once." Write down one guess for the cause and one thing you would check to test it

**Your answer:**

> I would guess that AligntoTag is not letting the teammate to control the robot. 

**30.** Pick one number in `constants.py` marked as a placeholder. How would you find the real value on the robot?

**Your answer:**

>ROBOT_TO_QUEST measures the distance from themiddle of the robot to the quest. To find the real value, we would use a ruler to figure out the distance.
