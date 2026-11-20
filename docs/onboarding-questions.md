# Learning the Robot Code: Questions

Read the files in the order below and answer each question in your own words. Type your answer after "Your answer:" (replace the empty `>` line), and write the file name where you found it. Short answers are fine. Run `robotpy sim` once before you start so you can see the robot move.

## Part 1: The big picture (robot.py, robotcontainer.py)

**1.** Which file starts the robot code, and what is the name of the main robot class inside it?

**Your answer:**

> The answer is robot.py and the main class is MyRobot

**2.** Find the functions in `robot.py` that end in `_init`, like `teleop_init`. When do you think each one runs?

**Your answer:**

> the main init initializes (creates) the class, autonomous runs when auton starts, teleop runs when teleop starts and ends auton, disabled init runs when the bot needs to be disabled and stops the robot, utility runs the robot when in utlity mode and spins the motors one by one to check if the motors are working.

**3.** What is `RobotContainer` used for? Name two things it creates

**Your answer:**

> It is used to create the drivetrain, questnav and controller input

**4.** Where is the controller port number stored? Why keep numbers like that in one place instead of typing them everywhere?

**Your answer:**

> It is the constant folder under the clss OIConstants and having it stored there makes it easier to modify and access throughout the files.

**5.** Which file has the drivetrain code, and which file has the numbers (like max speed)?

**Your answer:**

> The drivetrain code is in subsystem/drivetrain.py and constants.py holds the numbers 

**6.** Describe what happens from the moment the driver pushes a joystick to the moment the wheels spin. Name each file the action passes through

**Your answer:**

> First it initializes the robot and controller in robotcontainer, drive.py recieves an input and drivetrain creates the speed and direction each motor has to go and swerve module communicates to each motor where they have to go.

## Part 2: Commands and subsystems (commands/, subsystems/)

**7.** What is a subsystem? Give one example from this repo

**Your answer:**


> A subsystem is a section of the robot that performs a task nessecary but not related to the rest of the robot. eg: questnav  

**8.** What is a command? Give one example from this repo

**Your answer:**

> A command are class that tell the robot to do a certain tasks eg: SpinAllMotors

**9.** In your own words, how is a subsystem different from a command?

**Your answer:**

> Subsystems are the part of the robots. While commands are more like files

**10.** What does `add_requirements(drivetrain)` do? What could go wrong without it?

**Your answer:**

> It essentially priortizes that subsystem for that command.

**11.** What is a default command? Which one does the drivetrain have?

**Your answer:**

> A default command is the command that the subsystem does when it is recieving no inputs, the drivetrain's default command is Drive By Controller 

**12.** What happens to the robot when the driver holds the A button, then lets go?

**Your answer:**

> The robot runs align and goes to 1m in front of an april_tag and aligns it, when A is released it stops the wheels and gives back control to the driver.

**13.** A command has `initialize`, `execute`, `is_finished`, and `end`. Pick one command and say what each one does

**Your answer:**

> In AlignToTag intiaize resets all the steering values and execute will start, if it doesn't know where it is or an error occurs it hands back control to the driver. There is also no is_finsished as it automatically ends when A is released (end runs when you let go and removes the target marking and gives back control to the controller)

**14.** Read `demo_auto` in `commands/auto.py`. List the steps the robot does, in order

**Your answer:**

>  1. Drives Forward 2. Drives Left. 3.Spins forward.

## Part 3: Object-oriented programming (all files)

**15.** What is a class? Pick one from the repo and say what it represents

**Your answer:**

> A class is essentially a blueprint that can be used to create instantces of said class that can be executed constantly. eg: MyRobot

**16.** What is an object? How many `SwerveModule` objects get made, and where?

**Your answer:**

> An object is an instance of a class, and there are 4 "Swerve Modules" in drivetrain and they are made in drivetrain.py and line 57 

**17.** What does `self` mean inside a class?

**Your answer:**
self refers to an object/instance of that class

> 

**18.** Some variable names start with an underscore, like `self._drivetrain`. What do you think that tells other programmers?

**Your answer:**

>  Would indicate that that variable is only to be used within the class.
**19.** `Drivetrain` owns four `SwerveModule` objects. Why is that better than copying the module code four times?

**Your answer:**

> It allows us to be able to modify any constants more easily and allows us to not copy paste the same thing ten times
**20.** Why does `constants.py` exist? Name three constants and what they are for

**Your answer:**

> constants.py exists as it easy way for us to store variables and modify them without having to go into every file constantly. eg: DebugConstants.SPIN_VOLTS (controls max voltage)\, AlignConstants.FIELD (gi ves the bot a field reference), and OIConstants.DRIVER_CONTROLLER_PORT (defines the port that we refer to for the controler)
## Part 4: Swerve and simulation (subsystems/, docs/simulation.md)

**21.** What makes a swerve drive different from a tank drive?

**Your answer:**

> Swerve Drive has 8 motors giving it more control and the ability to move diagonally (1 motor to turn one for speed) while tank drive has only two and has less wave of motion. 

**22.** What is the difference between field-relative and robot-relative driving? Which one does the driver want in teleop?

**Your answer:**

> The driver wants robot-related driving as it controls the robot based on the position of the robot, while field relative makes the bot move on the direction of the field which is used for driving in swerve.

**23.** Each swerve module has three hardware devices. Name them and say what each one does

**Your answer:**

> the encoder tells the angle where the wheel is oriented, the drive motors changes the speed of the wheel, steer motors change the angle of the wheel. 

**24.** What is simulation? Name two things you can test without a real robot

**Your answer:**

> Runs our computer in a 3d modeled pretend enviorment, and it helps us test autonomous and the drive train, even if the bot isn't prepared yet. 

**25.** What do `robotpy sim` and `robotpy test` each do?

**Your answer:**

> Robotpy sim starts the simulation and robotpy test runs automated test and gives us a pass or fail..

## Part 5: Short exercises
 
**26.** Draw a diagram with a box for each of these: `MyRobot`, `RobotContainer`, `Drivetrain`, `DriveByController`, `AlignToTag`, `SwerveModule`. Draw arrows to show which one creates, uses, or controls which. Label each arrow

**Your answer:** (attach a photo or drawing, or paste the file name here)

> 

**27.** Say how you would add a button so that pressing B resets the robot's position to the starting spot. Which file do you edit, and which existing function do you call? (Hint: look for `reset_pose`)

**Your answer:**

> I would say self.driver_controller.b().while_true(Drivetrain.reset_pose())


**28.** Plan a new `Intake` subsystem with one motor. Which files would you create or change? What two functions would it need?

**Your answer:**

> I would create a new subsystem file called Intake initate it in robotcontainer and bind a button, and create a command file to recieve inputs from the controller/auton, add can_ID and speed in constants

**29.** A teammate says "the robot ignores my joysticks after I hold A once." Write down one guess for the cause and one thing you would check to test it

**Your answer:**

> Most likely the function giving back control to the user after align_to is not working or is not intiated, so if that were the case, I would check that function and look for any logical errors and/or syntax errors.
**30.** Pick one number in `constants.py` marked as a placeholder. How would you find the real value on the robot?
        
**Your answer:**

> Robot_to_Quest and consult design/Fab for details (Trust me)