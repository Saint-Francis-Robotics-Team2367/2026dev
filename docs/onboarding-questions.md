# Learning the Robot Code: Questions

Read the files in the order below and answer each question in your own words. Type your answer after "Your answer:" (replace the empty `>` line), and write the file name where you found it. Short answers are fine. Run `robotpy sim` once before you start so you can see the robot move.

## Part 1: The big picture (robot.py, robotcontainer.py)

**1.** Which file starts the robot code, and what is the name of the main robot class inside it?

**Your answer:**

> robot.py starts the robot code, and the class is MyRobot

**2.** Find the functions in `robot.py` that end in `_init`, like `teleop_init`. When do you think each one runs?

**Your answer:**

> __init__ runs when the code is started, and it sets up the foundation for the robot's code.
>autonomous_init runs when the autonomous part of the code starts
>teleop_init runs when teleop starts and ends the autonomous period
>disabled_init runs when the robot is disabled
>utility_init runs when the robot is in utility mode. it would spin the motors one by one to check functionality.

**3.** What is `RobotContainer` used for? Name two things it creates

**Your answer:**

> It puts all of the parts of the robot together. It makes drivetrain and driver_controllers

**4.** Where is the controller port number stored? Why keep numbers like that in one place instead of typing them everywhere?

**Your answer:**

> it is in the OIconstants class in the constants.py file. It is stored like this to keep it more organized and easy to change/update

**5.** Which file has the drivetrain code, and which file has the numbers (like max speed)?

**Your answer:**

> subsystems/drivetrain.py has the drivetrain code, while the numbers are in constants.py

**6.** Describe what happens from the moment the driver pushes a joystick to the moment the wheels spin. Name each file the action passes through

**Your answer:**

> starts at robotcontainer.py, goes to drive.py, then to drivetrain.py, to swervemodule.py, then sends the signals to the motors.

## Part 2: Commands and subsystems (commands/, subsystems/)

**7.** What is a subsystem? Give one example from this repo

**Your answer:**

> a subsystem is a smaller system that resides within a larger main system. one example would be the drivetrain subsystem or the questnav. in this case, it is a part of the robot that functions separately from others

**8.** What is a command? Give one example from this repo

**Your answer:**

> it is something given to a computer to perform a certain action. one example would be SpinAllMotors. 

**9.** In your own words, how is a subsystem different from a command?

**Your answer:**

> A subsystem is a part of the robot, whereas a command is telling the robot to use the subsystems to perform an action

**10.** What does `add_requirements(drivetrain)` do? What could go wrong without it?

**Your answer:**

> it tells the scheduler that the given job needs to involve the drivetrain

**11.** What is a default command? Which one does the drivetrain have?

**Your answer:**

> A default command is what the subsystem runs when nothing else is being received. The default command for the drivetrain is DriveByController

**12.** What happens to the robot when the driver holds the A button, then lets go?

**Your answer:**

> The AlignToTag command starts, the robot drives to a spot which is 1m in front of the AprilTag and stays there. If you let go, the task stops, the wheels stop, and joystick controls come back. 

**13.** A command has `initialize`, `execute`, `is_finished`, and `end`. Pick one command and say what each one does

**Your answer:**

> In AlignToTag:

    > Initalize clears steering math, then draws a line to the target on the field.
    > Execute runs over and over again and if robot knows where it is, it will drive towards the tag.
    > is_finished is not in AlignToTag since it ends when the A button is released. 
    > end runs when you let go of A. It stops the robot and removes the target marking while logging that a line was released. 

**14.** Read `demo_auto` in `commands/auto.py`. List the steps the robot does, in order

**Your answer:**

> The robot goes forward, then strafes left, spins, and finally stops. It drives at 1m/s and turns at pi/2


## Part 3: Object-oriented programming (all files)

**15.** What is a class? Pick one from the repo and say what it represents

**Your answer:**

> a class is a blueprint used to create objects. an example would be questnavsubsystem

**16.** What is an object? How many `SwerveModule` objects get made, and where?

**Your answer:**

> An object is a instance of a class. 4 swervemodule objects get made in the drivetrain.py file. They're called FL, FR, BL, BR.

**17.** What does `self` mean inside a class?

**Your answer:**

> self refers to an instance/object of that class.

**18.** Some variable names start with an underscore, like `self._drivetrain`. What do you think that tells other programmers?

**Your answer:**

> it indicates that the variable should only be used by a specific class and should not be changed by others.

**19.** `Drivetrain` owns four `SwerveModule` objects. Why is that better than copying the module code four times?

**Your answer:**

> It allows for more variance between the modules rather than all of them being the same. More precision is possible. It is easier to change one rather than all of them. 

**20.** Why does `constants.py` exist? Name three constants and what they are for

**Your answer:**

> to keep all needed constants in one spot, easy to reference. there are four constants keeping track of module locations relative to the robot center: 
    > FRONT_LEFT_LOCATION
    >FRONT_RIGHT_LOCATION
    >BACK_LEFT_LOCATION
    >BACK_RIGHT_LOCATION

## Part 4: Swerve and simulation (subsystems/, docs/simulation.md)

**21.** What makes a swerve drive different from a tank drive?

**Your answer:**

> Swerve drive can drive diagonally, while tank drive cannot. Tank needs two motors to function, while swerve needs 8.

**22.** What is the difference between field-relative and robot-relative driving? Which one does the driver want in teleop?

**Your answer:**

> Robot-relative is when forward is towards the front of the robot, while field-relative is when forward is always to the front of the field. Field-relative is what would be used for teleop. 

**23.** Each swerve module has three hardware devices. Name them and say what each one does

**Your answer:**

> The encoder (measures the angle to know where it's going), drive (spins the wheel to a set speed), and steer (points the robot in the right direction). 

**24.** What is simulation? Name two things you can test without a real robot

**Your answer:**

> A simulation is testing the robot on our computer with a pretend environment. two things you can test without a robot is test autonomous code, and testing if drive works.

**25.** What do `robotpy sim` and `robotpy test` each do?

**Your answer:**

> robotpy sim runs the WPILib Simulation GUI and robotpy test runs headless smoke test (checks for faults and gives a pass or fail)

## Part 5: Short exercises

**26.** Draw a diagram with a box for each of these: `MyRobot`, `RobotContainer`, `Drivetrain`, `DriveByController`, `AlignToTag`, `SwerveModule`. Draw arrows to show which one creates, uses, or controls which. Label each arrow

**Your answer:** (attach a photo or drawing, or paste the file name here)

[text](IMG_0222.HEIC)

**27.** Say how you would add a button so that pressing B resets the robot's position to the starting spot. Which file do you edit, and which existing function do you call? (Hint: look for `reset_pose`)

**Your answer:**

> drivetrain.py has the reset_pose method, which you can add to configure_bindings in robotcontainer.py. 

**28.** Plan a new `Intake` subsystem with one motor. Which files would you create or change? What two functions would it need?

**Your answer:**

> i would create a file called intake.py into the subsystems folder. It would need a function of spinning the motor and spinning the motor the opposite way. It would also need a class called Intake. Add motors's CAN in constants.py. In robotcontainer,py, create the intake.

**29.** A teammate says "the robot ignores my joysticks after I hold A once." Write down one guess for the cause and one thing you would check to test it

**Your answer:**

> One thing that could cause that is the function to give control back from align to the driver isn't working. A check you could do is to look at the code to check for logical errors. 

**30.** Pick one number in `constants.py` marked as a placeholder. How would you find the real value on the robot?

**Your answer:**

> ROBOT_TO_QUEST measures where the quest is compared to the center of the robot. In order to find the real value, you would use the ruler tool to figure out how far away the quest is from the middle. 
