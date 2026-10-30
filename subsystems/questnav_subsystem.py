"""QuestNav subsystem: feeds the headset's pose into the drivetrain's estimator.

The headset reports its *own* field pose at 100 Hz (VIO, corrected on-headset by
AprilTags when it sees them). Each loop this subsystem drains the unread frames,
converts headset pose to robot pose through the mount offset, and fuses it with
``Drivetrain.add_vision_measurement``. Frames are skipped while the headset is not
tracking. With no headset connected (e.g. simulation) it is a no-op.
"""

import commands2
import telemetry
from wpimath import Pose2d, Pose3d

from constants import QuestNavConstants as QC
from questnav import QuestNav
from subsystems.drivetrain import Drivetrain


class QuestNavSubsystem(commands2.Subsystem):
    def __init__(self, drivetrain: Drivetrain, questnav: QuestNav | None = None):
        super().__init__()
        self._drivetrain = drivetrain
        self._questnav = questnav or QuestNav(expected_version=QC.EXPECTED_APP_VERSION)
        self._quest_to_robot = QC.ROBOT_TO_QUEST.inverse()

    @property
    def questnav(self) -> QuestNav:
        return self._questnav

    def reset_pose(self, robot_pose: Pose2d) -> None:
        """Tell the headset where the robot is (it re-origins to match).

        Only needed without AprilTag correction, or to recover from a bad
        estimate; the drivetrain estimator is reset separately.
        """
        quest_pose = Pose3d(robot_pose).transform_by(QC.ROBOT_TO_QUEST)
        self._questnav.set_pose(quest_pose)

    def periodic(self) -> None:
        self._questnav.command_periodic()

        accepted = 0
        for frame in self._questnav.get_all_unread_pose_frames():
            if not frame.is_tracking:
                continue
            robot_pose = frame.quest_pose.transform_by(self._quest_to_robot)
            self._drivetrain.add_vision_measurement(
                robot_pose.to_pose2d(), frame.data_timestamp, QC.STD_DEVS
            )
            accepted += 1

        telemetry.log("QuestNavStatus/connected", self._questnav.is_connected())
        telemetry.log("QuestNavStatus/tracking", self._questnav.is_tracking())
        telemetry.log("QuestNavStatus/framesFused", accepted)
        battery = self._questnav.get_battery_percent()
        if battery is not None:
            telemetry.log("QuestNavStatus/batteryPercent", battery)
