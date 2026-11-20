# Learning the Robot Code: Questions

Read the files in the order below and answer each question in your own words. Type your answer after "Your answer:" (replace the empty `>` line), and write the file name where you found it. Short answers are fine. Run `robotpy sim` once before you start so you can see the robot move.

## Part 1: The big picture (robot.py, robotcontainer.py)

**1.** Which file starts the robot code, and what is the name of the main robot class inside it?

**Your answer:**

> robot.py is the file that starts the code. The main robot class is MyRobot 

**2.** Find the functions in `robot.py` that end in `_init`, like `teleop_init`. When do you think each one runs?

**Your answer:**

> _init builds the entire robot and runs when the code starts. autonomous_init runs when autonomous starts. teleop_init runs when teleop starts and ends autonomous period. disabled_init runs when the robot is disabled. utility_init runs when the robot is in utility mode: it would spin the motors one by one to check functionality.

**3.** What is `RobotContainer` used for? Name two things it creates

**Your answer:**

> RobotContainer is where the different pieces of the robot get put together in the code. It creates the drivetrain and the driver controller bindings.

**4.** Where is the controller port number stored? Why keep numbers like that in one place instead of typing them everywhere?

**Your answer:**

> The controller port is in constants.py inside of the OIConstants class. Having it as a shared number in one places means that if we have to change it we only have to do so in one place.

**5.** Which file has the drivetrain code, and which file has the numbers (like max speed)?

**Your answer:**

> Drivetrain code is inside the subsystem\drivetrain.py and the file with the numbers is constants.py.

**6.** Describe what happens from the moment the driver pushes a joystick to the moment the wheels spin. Name each file the action passes through

**Your answer:**

> The controller is first created in robotcontainer.py. Then the drive.py then reads the input on the jopysticks and turns that into spped usoing maximum speed variables form constant.py. subsystem/drivetrain.py turns these drive instructions into a speed and angle for each wheel. Then the swervemodule.py makes sure that each wheel moves to that speed and angle.

## Part 2: Commands and subsystems (commands/, subsystems/)

**7.** What is a subsystem? Give one example from this repo

**Your answer:**

> A subsystem is one part of the robot and the code that goes along with it. Drivetrain in subsystems/drivetrain.py.

**8.** What is a command? Give one example from this repo

**Your answer:**

> A command is one job the robot does for a while. DriveByController

**9.** In your own words, how is a subsystem different from a command?

**Your answer:**

> A subsystem is the part like the drivetrain while a command is the one that does the actions you ask that specific part of the robot to do like drive.

**10.** What does `add_requirements(drivetrain)` do? What could go wrong without it?

**Your answer:**

> it tells the shcduler that the job requires the drivetrain. Since only one job can use it at once this allows things like align to happen and block driving form occuring at the same time. WIhtout it aligning nad dirivng can send commands ot the wheels at the same time.

**11.** What is a default command? Which one does the drivetrain have?

**Your answer:**

> A default command is the job a subsystem does whenever nothing else is using it. The drivetrains default is DriveByController

**12.** What happens to the robot when the driver holds the A button, then lets go?

**Your answer:**

> The AlignToTag starts. The robot drives to a spot with is 1 meter in front of the AprilTag and stays there. If you let go, the job stops, the wheels stop, and joystick controls come back.

**13.** A command has `initialize`, `execute`, `is_finished`, and `end`. Pick one command and say what each one does

**Your answer:**

> AlignToTag: initialize runs once at the start and it clears the steering math, draws the target on the field, and then adds the target spot to the log. The execute runs over and over and if the robot knows where it is, it drives toward the tag but if it does not it returns to joystick control. is_finished is not in this one as it keeps going until you let go of A. end runs when you let go. It stops the robot, removes the target marking, and logs that align was released.

**14.** Read `demo_auto` in `commands/auto.py`. List the steps the robot does, in order

**Your answer:**

> Drive forward at 1m/s. Slide left at 1m/s. Spin in place. Stops

## Part 3: Object-oriented programming (all files)

**15.** What is a class? Pick one from the repo and say what it represents

**Your answer:**

> A class is a blueprint for a thing to be created. Drivetrain is the blueprint for the robot's drive system that we use throughout the robot code.

**16.** What is an object? How many `SwerveModule` objects get made, and where?

**Your answer:**

> An object is a instance built from a class. 4 SwerveModule objects are made inside Drivetrain.__init. Their names are FL, FR, BL, BR.

**17.** What does `self` mean inside a class?

**Your answer:**

> self means that it belongs to that specific object.

**18.** Some variable names start with an underscore, like `self._drivetrain`. What do you think that tells other programmers?

**Your answer:**

> a name like this would say that it is for the class's own use only and other files shuld use the public methods and leave that variable alone.

**19.** `Drivetrain` owns four `SwerveModule` objects. Why is that better than copying the module code four times?

**Your answer:**

> Drivetrain builds 4 SwerveModule objects from one class. A fix that is written to a method is adopted by all of them. These different parts only differ by their ids and ane sand driving directions which comes form the constants.

**20.** Why does `constants.py` exist? Name three constants and what they are for

**Your answer:**

> Constants.py is the place where all robot constants numbers are stored. Having them all in one place allows them the behavior of the robot to stay seperate from these constant values. DriveConstant.Max_SPEED_MPS which is the fastest speed the robot is allowed to drive. OIConstants.DRIVER_CONTROLLER_PORT: which USB port the driver controller is on. AlignConstants.STANDOFF_M: how far in front of the AprilTag the robot should stop when aligning.

## Part 4: Swerve and simulation (subsystems/, docs/simulation.md)

**21.** What makes a swerve drive different from a tank drive?

**Your answer:**

> A tank drive has left wheels and right wheels that only move forward and backward. It turns by running one faster than the other. A swerve drive has a wheel at the corner that cna spin and also role. So each whlee can point any direciton allowing it to move forward, sideways, or diagonally

**22.** What is the difference between field-relative and robot-relative driving? Which one does the driver want in teleop?

**Your answer:**

> Robot relative is forward means where the robot is pointing while the field relative is forward means down the field. Teleop uses field relative.

**23.** Each swerve module has three hardware devices. Name them and say what each one does

**Your answer:**

> It has drive TalonFX which spins the wheel to set speed
> It has steer TalonFX which turns the wheel to point it
> It has the CANcoder/encoder which measures the wheel's angle so the steer motor knows where it is currently pointing.

**24.** What is simulation? Name two things you can test without a real robot

**Your answer:**

> Simulation is a pretend robot on your computer. Two things you canh do is run demo_auto and test drive the robot in teleop and see the robot move on the field.

**25.** What do `robotpy sim` and `robotpy test` each do?

**Your answer:**

> robotpy sim opens the simulation window so you can watch and drive the robot on your device while the robotpy test runs automated checks and gives us a pass or fail on it.

## Part 5: Short exercises

**26.** Draw a diagram with a box for each of these: `MyRobot`, `RobotContainer`, `Drivetrain`, `DriveByController`, `AlignToTag`, `SwerveModule`. Draw arrows to show which one creates, uses, or controls which. Label each arrow

**Your answer:** (attach a photo or drawing, or paste the file name here)

> [Drawing](IMG_0222.HEIC)

**27.** Say how you would add a button so that pressing B resets the robot's position to the starting spot. Which file do you edit, and which existing function do you call? (Hint: look for `reset_pose`)

**Your answer:**

> Edit robotcontainer.py, inside configure_bindings. Make b call reset_pose on the drivetrain, which would sets x and y to be 0 and the robot facing forward.

**28.** Plan a new `Intake` subsystem with one motor. Which files would you create or change? What two functions would it need?

**Your answer:**

> Create a new file inside the subsystem folder called intake.py with a class called Intake. Create functions for it to be able to have functionality. Add the motor's CAN id and its speeds we want into cosntant.py. In robotcontainer.py, create the intake and bind a button to it to make it function.

**29.** A teammate says "the robot ignores my joysticks after I hold A once." Write down one guess for the cause and one thing you would check to test it

**Your answer:**

> I would guess that the AlignToTag is still controlling the robot and not allowing the controller to control the robot. I would think that ALignToTag is still running so I would check the log for the line when it was released. If it was never release then it is still active.

**30.** Pick one number in `constants.py` marked as a placeholder. How would you find the real value on the robot?

**Your answer:**

> QuestNavConstants.ROBOT_TO_QUEST: I would measure from the center of the robot to the headseat to find how far forward, how far left, and how high it is, and which way it faces.
