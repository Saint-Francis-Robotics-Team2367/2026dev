"""Hold-to-align: drive to a spot 1 m in front of a field AprilTag and hold it.

The target is fixed: the tag's pose from the WPILib field layout, moved
``STANDOFF_M`` out along the tag's normal and turned to face the tag. Each loop,
P controllers on field x, y, and heading drive the pose estimate (wheel odometry
fused with QuestNav) to that target, field-relative.

It only aligns while ``QuestNavSubsystem.pose_trusted()`` (a tracking headset on a
real robot; always in simulation); otherwise the driver keeps normal stick control
until it is trusted again.
"""

import math

import robotpy_fields
import telemetry
from commands2 import Command
from commands2.button import CommandNiDsXboxController
from robotpy_fields import FieldId
from wpimath import PIDController, Pose2d, Rotation2d, Transform2d

from commands.drive import stick_velocities
from constants import AlignConstants as AC
from dslog import log
from subsystems.drivetrain import Drivetrain
from subsystems.questnav_subsystem import QuestNavSubsystem


def standoff_pose(tag_pose: Pose2d, standoff_m: float) -> Pose2d:
    """The robot pose ``standoff_m`` out from a tag's face, front facing the tag.

    A WPILib tag pose's +x axis points out of the tag's face, so step out along it,
    then turn around.
    """
    return tag_pose.transform_by(Transform2d(standoff_m, 0.0, Rotation2d(math.pi)))


def tag_target_pose(
    tag_id: int, field: FieldId = AC.FIELD, standoff_m: float = AC.STANDOFF_M
) -> Pose2d:
    """The align target for ``tag_id`` on ``field``; raises if the tag isn't there."""
    tag_pose = robotpy_fields.get_field(field).get_tag_pose(tag_id)
    if tag_pose is None:
        raise ValueError(
            f"AprilTag {tag_id} is not in the {robotpy_fields.get_field_name(field)} "
            "layout; check AlignConstants.TARGET_TAG_ID / FIELD"
        )
    return standoff_pose(tag_pose.to_pose2d(), standoff_m)


class AlignToTag(Command):
    """While scheduled, drives to and holds the target pose (never finishes)."""

    def __init__(
        self,
        drivetrain: Drivetrain,
        questnav: QuestNavSubsystem,
        controller: CommandNiDsXboxController,
        tag_id: int = AC.TARGET_TAG_ID,
    ) -> None:
        super().__init__()
        self._drivetrain = drivetrain
        self._questnav = questnav
        self._controller = controller
        self._tag_id = tag_id
        # Resolved now so a bad tag ID fails at robot startup, not mid-match.
        self._target = tag_target_pose(tag_id)
        self._x = PIDController(AC.TRANSLATION_KP, 0.0, 0.0)
        self._y = PIDController(AC.TRANSLATION_KP, 0.0, 0.0)
        self._heading = PIDController(AC.HEADING_KP, 0.0, 0.0)
        self._heading.enable_continuous_input(-math.pi, math.pi)
        # None until the first loop, so the starting state is always logged.
        self._aligning: bool | None = None
        self.add_requirements(drivetrain)

    @property
    def target(self) -> Pose2d:
        return self._target

    def initialize(self) -> None:
        for pid in (self._x, self._y, self._heading):
            pid.reset()
        self._aligning = None
        self._drivetrain.show_target(self._target)
        t = self._target
        log(
            f"[align] tag {self._tag_id}: target ({t.x:.2f}, {t.y:.2f}) m, "
            f"{t.rotation().degrees():.0f} deg"
        )

    def execute(self) -> None:
        can_align = self._questnav.pose_trusted()
        if can_align != self._aligning:
            self._aligning = can_align
            log(
                "[align] aligning"
                if can_align
                else "[align] QuestNav not tracking: driver keeps the sticks"
            )

        pose = self._drivetrain.get_pose()
        vx, vy, omega = (
            self.calculate(pose) if can_align else stick_velocities(self._controller)
        )
        self._drivetrain.drive(vx, vy, omega, field_relative=True)
        telemetry.log("Align/aligning", can_align)
        telemetry.log("Align/atTarget", self.at_target(pose))

    def end(self, interrupted: bool) -> None:
        self._drivetrain.drive(0.0, 0.0, 0.0, field_relative=True)
        self._drivetrain.show_target(None)
        telemetry.log("Align/aligning", False)
        log("[align] released")

    def calculate(self, pose: Pose2d) -> tuple[float, float, float]:
        """Field-relative (vx, vy, omega) that moves ``pose`` toward the target."""
        vx = self._x.calculate(pose.x, self._target.x)
        vy = self._y.calculate(pose.y, self._target.y)
        # Cap the speed along the path, not per axis, so diagonals aren't faster.
        speed = math.hypot(vx, vy)
        if speed > AC.MAX_SPEED_MPS:
            vx, vy = vx * AC.MAX_SPEED_MPS / speed, vy * AC.MAX_SPEED_MPS / speed
        omega = self._heading.calculate(
            pose.rotation().radians(), self._target.rotation().radians()
        )
        omega = max(-AC.MAX_ANGULAR_SPEED_RPS, min(AC.MAX_ANGULAR_SPEED_RPS, omega))
        return vx, vy, omega

    def at_target(self, pose: Pose2d) -> bool:
        error = pose.relative_to(self._target)
        return (
            error.translation().norm() <= AC.POSITION_TOLERANCE_M
            and abs(error.rotation().radians()) <= AC.HEADING_TOLERANCE_RAD
        )
