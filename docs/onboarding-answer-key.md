# Mentor Answer Key

For `docs/onboarding-questions.md`. Keep this file away from students until they finish.


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
