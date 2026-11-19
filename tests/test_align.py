"""Hold-A align-to-tag: target geometry, controller output, fallback, and binding.

Phoenix's simulated motors run on wall-clock time, so these check the command's
math and decisions with fakes rather than waiting for the robot to converge; watch
convergence in ``robotpy sim`` by holding A.
"""

import math

import commands2
import pytest
import wpilib
from wpilib.simulation import DriverStationSim, NiDsXboxControllerSim
from wpimath import Pose2d, Rotation2d

import commands.align as align
from commands.align import AlignToTag, standoff_pose, tag_target_pose
from constants import AlignConstants, DriveConstants, OIConstants


class _FakeDrivetrain(commands2.Subsystem):
    def __init__(self, pose: Pose2d = Pose2d()) -> None:
        super().__init__()
        self.pose = pose
        self.drives: list[tuple[float, float, float, bool]] = []
        self.targets: list[Pose2d | None] = []

    def get_pose(self) -> Pose2d:
        return self.pose

    def drive(self, vx, vy, omega, field_relative=True) -> None:
        self.drives.append((vx, vy, omega, field_relative))

    def show_target(self, pose) -> None:
        self.targets.append(pose)


class _FakeQuestNav:
    def __init__(self, tracking: bool) -> None:
        self.tracking = tracking

    def is_tracking(self) -> bool:
        return self.tracking


class _FakeController:
    """Raw HID axes: forward is -Y, left is -X (as on a real pad)."""

    def __init__(self, left_x=0.0, left_y=0.0, right_x=0.0) -> None:
        self.left_x, self.left_y, self.right_x = left_x, left_y, right_x

    def get_left_x(self) -> float:
        return self.left_x

    def get_left_y(self) -> float:
        return self.left_y

    def get_right_x(self) -> float:
        return self.right_x


def _command(
    pose: Pose2d = Pose2d(), tracking: bool = True, controller=None
) -> tuple[AlignToTag, _FakeDrivetrain]:
    drivetrain = _FakeDrivetrain(pose)
    command = AlignToTag(
        drivetrain,  # type: ignore[arg-type]
        _FakeQuestNav(tracking),  # type: ignore[arg-type]
        controller or _FakeController(),  # type: ignore[arg-type]
    )
    return command, drivetrain


# --- Target geometry --------------------------------------------------------


def test_standoff_is_out_along_tag_normal_facing_the_tag() -> None:
    # A tag facing +y (90 deg): the robot sits 1 m toward +y, facing -y.
    target = standoff_pose(Pose2d(5.0, 2.0, Rotation2d.from_degrees(90)), 1.0)
    assert (target.x, target.y) == pytest.approx((5.0, 3.0), abs=1e-9)
    assert target.rotation().degrees() == pytest.approx(-90.0)


def test_placeholder_tag_target_is_one_meter_in_front() -> None:
    # Tag 26 (2026 Welded) is at (4.02, 4.03) facing the blue wall (180 deg).
    target = tag_target_pose(26)
    assert (target.x, target.y) == pytest.approx((3.022, 4.035), abs=1e-3)
    assert target.rotation().degrees() == pytest.approx(0.0, abs=1e-9)


def test_unknown_tag_fails_with_a_clear_error() -> None:
    with pytest.raises(ValueError, match="AprilTag 999 is not in"):
        tag_target_pose(999)


# --- Controller output ------------------------------------------------------


def test_drives_toward_target_and_stops_there() -> None:
    command, _ = _command()
    target = command.target

    near = Pose2d(target.x - 0.1, target.y + 0.1, target.rotation())
    vx, vy, omega = command.calculate(near)
    assert vx > 0 and vy < 0  # back toward the target on both axes
    assert omega == pytest.approx(0.0, abs=1e-9)
    assert not command.at_target(near)

    assert command.calculate(target) == pytest.approx((0.0, 0.0, 0.0), abs=1e-9)
    assert command.at_target(target)


def test_speed_is_capped_along_the_path() -> None:
    command, _ = _command()
    far = Pose2d(command.target.x - 10.0, command.target.y - 10.0, Rotation2d())
    vx, vy, _ = command.calculate(far)
    assert math.hypot(vx, vy) == pytest.approx(AlignConstants.MAX_SPEED_MPS)
    assert vx == pytest.approx(vy)  # still heading straight at it


def test_heading_takes_the_short_way_around() -> None:
    command, _ = _command()  # target faces 0 deg
    _, _, omega = command.calculate(
        Pose2d(command.target.translation(), Rotation2d.from_degrees(-10))
    )
    assert 0 < omega < math.radians(90)  # small CCW turn, not most of a lap
    _, _, omega = command.calculate(
        Pose2d(command.target.translation(), Rotation2d.from_degrees(179))
    )
    assert omega == pytest.approx(-AlignConstants.MAX_ANGULAR_SPEED_RPS)


# --- Tracking gate ----------------------------------------------------------


def test_real_robot_without_tracking_keeps_stick_control(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(align.wpilib.RobotBase, "is_simulation", lambda: False)
    lines: list[str] = []
    monkeypatch.setattr(align, "log", lines.append)
    stick = _FakeController(left_y=-1.0)  # full forward
    command, drivetrain = _command(tracking=False, controller=stick)

    command.initialize()
    command.execute()
    vx, vy, omega, field_relative = drivetrain.drives[-1]
    assert vx == pytest.approx(DriveConstants.MAX_SPEED_MPS)
    assert (vy, omega, field_relative) == (0.0, 0.0, True)
    assert any("not tracking" in line for line in lines)

    command._questnav.tracking = True  # type: ignore[attr-defined]
    command.execute()
    expected = command.calculate(drivetrain.pose)
    assert drivetrain.drives[-1][:3] == pytest.approx(expected)
    assert lines[-1] == "[align] aligning"


def test_simulation_aligns_without_a_headset() -> None:
    assert wpilib.RobotBase.is_simulation()
    command, drivetrain = _command(tracking=False)
    command.initialize()
    command.execute()
    assert drivetrain.drives[-1][:3] == pytest.approx(
        command.calculate(drivetrain.pose)
    )


def test_target_marker_shown_then_cleared_and_robot_stopped() -> None:
    command, drivetrain = _command()
    command.initialize()
    command.execute()
    command.end(True)
    assert drivetrain.targets == [command.target, None]
    assert drivetrain.drives[-1] == (0.0, 0.0, 0.0, True)


# --- Binding ----------------------------------------------------------------


def test_holding_a_schedules_align_and_release_cancels() -> None:
    from robotcontainer import RobotContainer

    scheduler = commands2.CommandScheduler.get_instance()
    container = RobotContainer()
    pad = NiDsXboxControllerSim(OIConstants.DRIVER_CONTROLLER_PORT)
    try:
        DriverStationSim.set_enabled(True)
        pad.set_a_button(True)
        pad.notify_new_data()
        DriverStationSim.notify_new_data()
        scheduler.run()
        assert scheduler.is_scheduled(container.align_command)

        pad.set_a_button(False)
        pad.notify_new_data()
        DriverStationSim.notify_new_data()
        scheduler.run()
        assert not scheduler.is_scheduled(container.align_command)
    finally:
        DriverStationSim.set_enabled(False)
        DriverStationSim.notify_new_data()
        scheduler.cancel_all()
        scheduler.unregister_all_subsystems()
        scheduler.get_active_button_loop().clear()


# --- Field-relative frame ---------------------------------------------------


def test_field_relative_drive_uses_the_estimated_heading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After a pose reset the gyro and estimate disagree; field +x must follow the
    estimate (otherwise aligning from a reset or QuestNav-corrected pose spirals)."""
    from subsystems.drivetrain import Drivetrain

    drivetrain = Drivetrain()
    sent: list = []
    for module in drivetrain._modules:
        monkeypatch.setattr(module, "set_desired_state", sent.append)

    # Raw gyro still reads 0 deg; the estimate now says the robot faces +y.
    drivetrain.reset_pose(Pose2d(1.0, 1.0, Rotation2d.from_degrees(90)))
    drivetrain.drive(1.0, 0.0, 0.0, field_relative=True)

    # Field +x is the robot's right, so every wheel points at -90 deg.
    assert len(sent) == 4
    for state in sent:
        assert state.angle.degrees() == pytest.approx(-90.0, abs=1.0) or (
            state.angle.degrees() == pytest.approx(90.0, abs=1.0) and state.velocity < 0
        )
