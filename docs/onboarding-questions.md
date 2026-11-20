# Learning the Robot Code: Questions

Read the files in the order below and answer each question in your own words. Type your answer after "Your answer:" (replace the empty `>` line), and write the file name where you found it. Short answers are fine. Run `robotpy sim` once before you start so you can see the robot move.

## Part 1: The big picture (robot.py, robotcontainer.py)

**1.** Which file starts the robot code, and what is the name of the main robot class inside it?

**Your answer:**
robot.py is the file. it has the class MyRobot
> 

**2.** Find the functions in `robot.py` that end in `_init`, like `teleop_init`. When do you think each one runs?

**Your answer:**
__init builds the foundation of the robot
autonomous_init runs when autonomous starts
teleop_init runs when teleop starts and ends autonomous
disabled_init disables the robot and stops moving
utility_init can see status of all motors. runs when robot in utility mode, spins motors one by one
> 

**3.** What is `RobotContainer` used for? Name two things it creates

**Your answer:**
questNav
drivetrain
put all peices together and makes them functional together
> 

**4.** Where is the controller port number stored? Why keep numbers like that in one place instead of typing them everywhere?

**Your answer:**
in constants.py in class OIConstants. we can keep track of all the constants and is easy to find and change
> 

**5.** Which file has the drivetrain code, and which file has the numbers (like max speed)?

**Your answer:**
in subsystems/drivetrain.py. constants.py
> 

**6.** Describe what happens from the moment the driver pushes a joystick to the moment the wheels spin. Name each file the action passes through

**Your answer:**
creates controller robotcontainer.py
finds position of the stick drive.py
creates speed in angle drivetrain.py
sends signal swervemodule.py
> 

## Part 2: Commands and subsystems (commands/, subsystems/)

**7.** What is a subsystem? Give one example from this repo

**Your answer:**
drivetrain.py
it does a specific part of a robot
> 

**8.** What is a command? Give one example from this repo

**Your answer:**
SpinAllMotors(Command)
it tells the subsystems what to do from given imputs
> 

**9.** In your own words, how is a subsystem different from a command?

**Your answer:**
subsystem is a file with many commands that is an actually a part of the robot
> 

**10.** What does `add_requirements(drivetrain)` do? What could go wrong without it?

**Your answer:**
it tells scheduler that it needs to use drivetrain now
it can be driving and aligning
it prioritizes debug and align over driving
> 

**11.** What is a default command? Which one does the drivetrain have?

**Your answer:**
it is the basic thing that the robot does when no other modes
drivetrain has DriveByController(Command) which drives
> 

**12.** What happens to the robot when the driver holds the A button, then lets go?

**Your answer:**
the AlignToTag(Command) starts and robot drives 1 meter away from april tag, aligns, drive stops motor stops and control comes back
> 

**13.** A command has `initialize`, `execute`, `is_finished`, and `end`. Pick one command and say what each one does

**Your answer:**
AlignToTag(Command)
clears steering math
draws where it is on the field from april tag

it starts running the command again
if it doesnt know where it is control is given back

no is_finished because it automatically ends

ends when you let go and gives back control 

**14.** Read `demo_auto` in `commands/auto.py`. List the steps the robot does, in order

**Your answer:**
Forward, then left, spin, stop 1 meter per second
> 

## Part 3: Object-oriented programming (all files)

**15.** What is a class? Pick one from the repo and say what it represents

**Your answer:**
it defines functions and commands
class MyRobot
> 

**16.** What is an object? How many `SwerveModule` objects get made, and where?

**Your answer:**
it is the instance for the class. 4 objects are made in line 59
for i, name in enumerate(("FL", "FR", "BL", "BR"))
> 

**17.** What does `self` mean inside a class?

**Your answer:**
the class uses self in front of a variable
refers to the instance of that class
> 

**18.** Some variable names start with an underscore, like `self._drivetrain`. What do you think that tells other programmers?

**Your answer:**
only the class can use it and other classes have to use a different methods
> 

**19.** `Drivetrain` owns four `SwerveModule` objects. Why is that better than copying the module code four times?

**Your answer:**
it is easier to look at and organize
you can change all at once and is easy to change quick
> 

**20.** Why does `constants.py` exist? Name three constants and what they are for

**Your answer:**
to state all the variables that stay the same
MAX_SPEED_MPS that is the max speed module can go
WHEEL_DIAMETER_M = 0.1016 that states the diameter of the wheel
TRACK_WIDTH_M = 0.5 distance stays the same
> 

## Part 4: Swerve and simulation (subsystems/, docs/simulation.md)

**21.** What makes a swerve drive different from a tank drive?

**Your answer:**
swerve: all wheels can spin and do diagonal 8 motors
tank: only foward back turn 2 motors
> 

**22.** What is the difference between field-relative and robot-relative driving? Which one does the driver want in teleop?

**Your answer:**
robot relative is from robot pov
field is from human pov
driver wants field relative to be able drive easier from what human sees
> 

**23.** Each swerve module has three hardware devices. Name them and say what each one does

**Your answer:**
encoder: looks at current wheel angle
drive: spins wheel to right speed
steer: angles the wheel
> 

**24.** What is simulation? Name two things you can test without a real robot

**Your answer:**
runs robot on computer in a fake enviorment
autonomous
drivetrain
> 

**25.** What do `robotpy sim` and `robotpy test` each do?

**Your answer:**
`robotpy sim` open simulation it behaves how it would normally and can be watched and controlled. `robotpy test` fast-forwards so not really realistic and is automated and checks for faults
> 

## Part 5: Short exercises

**26.** Draw a diagram with a box for each of these: `MyRobot`, `RobotContainer`, `Drivetrain`, `DriveByController`, `AlignToTag`, `SwerveModule`. Draw arrows to show which one creates, uses, or controls which. Label each arrow

**Your answer:** (attach a photo or drawing, or paste the file name here)

> [Drawing](<IMG_0222 (5).HEIC>)

**27.** Say how you would add a button so that pressing B resets the robot's position to the starting spot. Which file do you edit, and which existing function do you call? (Hint: look for `reset_pose`)

**Your answer:**
configure_bindings and change it to button B to call reset pose

> 

**28.** Plan a new `Intake` subsystem with one motor. Which files would you create or change? What two functions would it need?

**Your answer:**
create intake.py
function intake
put speed and id into constantes
in robotcontainer create intake and have a button to use it
> 

**29.** A teammate says "the robot ignores my joysticks after I hold A once." Write down one guess for the cause and one thing you would check to test it

**Your answer:**
after it aligns, the control wont be given back. check AlignToTag(Command) log to see if it stopped
> 

**30.** Pick one number in `constants.py` marked as a placeholder. How would you find the real value on the robot?

**Your answer:**

>
