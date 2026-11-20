# Learning the Robot Code: Questions

Read the files in the order below and answer each question in your own words. Type your answer after "Your answer:" (replace the empty `>` line), and write the file name where you found it. Short answers are fine. Run `robotpy sim` once before you start so you can see the robot move.

## Part 1: The big picture (robot.py, robotcontainer.py)

**1.** Which file starts the robot code, and what is the name of the main robot class inside it?

**Your answer:**

> The file is Robot.py and the name of the class is MyRobot.

**2.** Find the functions in `robot.py` that end in `_init`, like `teleop_init`. When do you think each one runs?

**Your answer:**

> The first init runs when you start the code and helps build the entire code for the robot. Autonomous init runs when autonomous start. Teleop init runs when teleop starts.disabled init runs when the robot is disabled. utility init when the robot is in utitlity mode, spins motors one by one to check fuctionality.
**3.** What is `RobotContainer` used for? Name two things it creates

**Your answer:**

> RobotContainer is used to store the systems. It creates the Drivetrain and the QuestNavSystem. Additionally, it creates the system for the controller.

**4.** Where is the controller port number stored? Why keep numbers like that in one place instead of typing them everywhere?

**Your answer:**

> It's stored in constants.py in OIConstants class. We store them in here to keep track of them better.

**5.** Which file has the drivetrain code, and which file has the numbers (like max speed)?

**Your answer:**

> The file that has the code is drivetrain.py which is in the subsystems and the file that has numbers is constants.py.

**6.** Describe what happens from the moment the driver pushes a joystick to the moment the wheels spin. Name each file the action passes through

**Your answer:**

> It starts a robotcontainer.py because these are where the information is stored, then when the joystick is moved, commands and functions from drive.py work, and information from constants.py are utlized.   

## Part 2: Commands and subsystems (commands/, subsystems/)

**7.** What is a subsystem? Give one example from this repo

**Your answer:**

> A subsystem is basically a system in charge of a different area that has its own file. Its assigned of executing a specific task specific to a given area. One example is questnav_subsystem.py

**8.** What is a command? Give one example from this repo

**Your answer:**

> A command is basically getting something a file-inputs or files-to commit a specific action. An example is class SpinAllMotors(Command): in debug.py.

**9.** In your own words, how is a subsystem different from a command?

**Your answer:**

> A subsystem is different from a command because a subsystem can be a file-system full of commands-assigned to complete a variety of tasks while a command is really for only for one task. Commands complete the actual task while subsystems are the part of robot.

**10.** What does `add_requirements(drivetrain)` do? What could go wrong without it?

**Your answer:**

> Self.add_requirements(drivetrain) is used to tell the scehduler that the drivetrain is needed and needs to be prioritized for that specific command. The task would not be performed efffeciently.

**11.** What is a default command? Which one does the drivetrain have?

**Your answer:**

> A default command is the command is the job a subsystem does when nothing else is happening. It stays idle and is awaiting for commands annd conditions to be met. The drivetrain default command is class DriveByController(Command):.
 

**12.** What happens to the robot when the driver holds the A button, then lets go?

**Your answer:**

> The align to tag starts, the robot then drives to a spot 1 meter to the april tage and stays there. If you let go, the job stops, the wheels stop, aand the joystick controls come back. 

**13.** A command has `initialize`, `execute`, `is_finished`, and `end`. Pick one command and say what each one does

**Your answer:**

> Intialize resets the steering math. AlignToTag intializes resets all the steering values. Execute will start, if it doesn't know where it is or an error occurs it hands back control to the driver. There is no is_finished because it automatically ends when A is released. End happends when you let go and removes the target marking and giving back control to the controller.

**14.** Read `demo_auto` in `commands/auto.py`. List the steps the robot does, in order

**Your answer:**

> It moves foward, moves left, and spins foward.

## Part 3: Object-oriented programming (all files)

**15.** What is a class? Pick one from the repo and say what it represents

**Your answer:**

> A class is assigning a name to a blueprint which allows to create objects and instances. One example is myrobot in robot.py.

**16.** What is an object? How many `SwerveModule` objects get made, and where?

**Your answer:**

> An object is an instance of a class. SwerveModule objects get made in drivetrain.py on line 59 in class Drivetrain(commands2.Subsystem):


**17.** What does `self` mean inside a class?

**Your answer:**

> Self refers to an instance or object related to that class. 

**18.** Some variable names start with an underscore, like `self._drivetrain`. What do you think that tells other programmers?

**Your answer:**

> It tells the programmers its different from what is being defined or set equal to. It tells the programmer it can only be accessed within the class and it is a "private variable."

**19.** `Drivetrain` owns four `SwerveModule` objects. Why is that better than copying the module code four times?

**Your answer:**

> This is better than copying the module code four times so each module can operate independently. Additionally, it is better for organization purposes.  

**20.** Why does `constants.py` exist? Name three constants and what they are for

**Your answer:**

> Constants.py exists to hold values/variables assigned to instances, objects or tasks. It allows for all variables to be in one place for a better reference point. Three constants are:
1. MAX_SPEED_MPS = 4.5-This sets the max speed
2. MAX_ANGULAR_SPEED_RPS = 2 * math.pi-This sets the max speed  
3. WHEEL_BASE_M = 0.5-This sets the size



## Part 4: Swerve and simulation (subsystems/, docs/simulation.md)

**21.** What makes a swerve drive different from a tank drive?

**Your answer:**

> Swerve drive can move more precise and can quickly turn while tank drive can only go foward a backward and change the speeds of the motors to turn.
**22.** What is the difference between field-relative and robot-relative driving? Which one does the driver want in teleop?

**Your answer:**

>Field-relative driving is autonomous with x-y coordinates and where the robot starts is the origin. It can move in any direction. Robot-relative bascially means the front of the robot has to face the direction it wants to go, its like a car. The driver wants field-relative in teleop.  

**23.** Each swerve module has three hardware devices. Name them and say what each one does

**Your answer:**

> 1. Encoder measures the wheel's angle so the steer moto know where it is currently. Steer decides where the wheel needs to turn. Drive measures how much the motor needs to spin.

**24.** What is simulation? Name two things you can test without a real robot

**Your answer:**

> A simulation is an imitation of a process. Without a robot, we can test autonomous systems and drivetrain to test the overall quality of the code.

**25.** What do `robotpy sim` and `robotpy test` each do?

**Your answer:**

> Robotpy sim connects to the simulation and starts it. and robotpy test starts the test part of the simualtion, runs automated checks, and gives us a pass or fail. 

## Part 5: Short exercises

**26.** Draw a diagram with a box for each of these: `MyRobot`, `RobotContainer`, `Drivetrain`, `DriveByController`, `AlignToTag`, `SwerveModule`. Draw arrows to show which one creates, uses, or controls which. Label each arrow

**Your answer:** (attach a photo or drawing, or paste the file name here)

> [Drawing](IMG_0222.HEIC)

**27.** Say how you would add a button so that pressing B resets the robot's position to the starting spot. Which file do you edit, and which existing function do you call? (Hint: look for `reset_pose`)

**Your answer:**

> The file I would edit would be container.py and the existing function I would call would be self.driver_controller.a().while_true(self.align_command). This would set x and y to be 0, 0 and the robot would be facing forward.
**28.** Plan a new `Intake` subsystem with one motor. Which files would you create or change? What two functions would it need?

**Your answer:**

> I would create a file called Intake.py. I would create a function for it to be able to have fuctionality. We would add the motors CAN id and its speed we want into constant.py In robocontainer.py, create the intake and bind a button to it to make a function. 

**29.** A teammate says "the robot ignores my joysticks after I hold A once." Write down one guess for the cause and one thing you would check to test it

**Your answer:**

> One guess would be that that the AligntoTag is still controlling the robot and not alloqing the controller to control the robot. The Aligntag would still be running so I would check the log to see if it was ever released.
**30.** Pick one number in `constants.py` marked as a placeholder. How would you find the real value on the robot?

**Your answer:**

>I would find the real value on the robot by saying robottoquest and manually measuring the values.
