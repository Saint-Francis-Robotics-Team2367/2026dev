"""QuestNav tests: wire codec, NT client, and pose fusion (HAL-free, plain pytest).

The golden hex strings were produced by the official protobuf compiler
(``grpc_tools.protoc``) from QuestNav's ``protos/``, so the hand-written codec is
checked against the reference encoding rather than against itself.
"""

import math

import pytest
import wpilib
from ntcore import NetworkTableInstance, PubSubOptions
from wpimath import Pose2d, Pose3d, Rotation2d, Rotation3d, Translation3d

from constants import QuestNavConstants
from questnav import QuestNav, protocol
from subsystems.questnav_subsystem import QuestNavSubsystem

# frame_count=1234, timestamp=56.789, pose (1.5, -2.25, 0.5) yawed 45 deg, tracking.
GOLDEN_FRAME = bytes.fromhex(
    "08d20911a245b6f3fd644c401a330a1b09000000000000f83f1100000000000002c0190000"
    "00000000e03f12140a1209468d32cf6b90ed3f2163a9aea6e27dd83f2001"
)
# tracking_lost_counter=3, battery_percent=87.
GOLDEN_DEVICE = bytes.fromhex("08031857")
# POSE_RESET, command_id=7, target (3, 4, 0.25) with identity rotation.
GOLDEN_COMMAND = bytes.fromhex(
    "08011007522c0a2a0a1b0900000000000008401100000000000010401900000000000"
    "0d03f120b0a0909000000000000f03f"
)
# command_id=7, success=false, error_message="nope".
GOLDEN_RESPONSE = bytes.fromhex("08071a046e6f7065")


def _frame_bytes(pose: Pose3d, frame_count: int = 1, tracking: bool = True) -> bytes:
    """Encode a frame the way the headset does (reuses the golden-checked pose codec)."""
    body = protocol.encode_pose3d(pose)
    return (
        bytes([0x08])
        + protocol._encode_varint(frame_count)
        + bytes([0x1A])
        + protocol._encode_varint(len(body))
        + body
        + (b"\x20\x01" if tracking else b"")
    )


# --- Codec ------------------------------------------------------------------


def test_decode_frame_matches_reference() -> None:
    frame = protocol.decode_frame_data(GOLDEN_FRAME)
    assert frame.frame_count == 1234
    assert frame.app_timestamp == pytest.approx(56.789)
    assert frame.is_tracking
    t = frame.quest_pose.translation()
    assert (t.x, t.y, t.z) == pytest.approx((1.5, -2.25, 0.5))
    assert frame.quest_pose.rotation().z_degrees == pytest.approx(45.0)


def test_decode_device_and_response() -> None:
    assert protocol.decode_device_data(GOLDEN_DEVICE) == protocol.DeviceData(3, 87)
    assert protocol.decode_command_response(
        GOLDEN_RESPONSE
    ) == protocol.CommandResponse(7, False, "nope")


def test_encode_pose_reset_matches_reference() -> None:
    pose = Pose3d(Translation3d(3.0, 4.0, 0.25), Rotation3d())
    assert protocol.encode_pose_reset_command(7, pose) == GOLDEN_COMMAND


def test_empty_frame_decodes_to_defaults() -> None:
    frame = protocol.decode_frame_data(b"")
    assert frame.frame_count == 0 and not frame.is_tracking


def test_negative_int32_and_unknown_fields() -> None:
    # frame_count=-5 is a 10-byte varint; field 5 is the int64 server_timestamp
    # newer headset builds add, which must be skipped.
    buf = bytes.fromhex("08fbffffffffffffffff01") + b"\x28\x96\x01"
    assert protocol.decode_frame_data(buf).frame_count == -5


def test_truncated_message_raises() -> None:
    with pytest.raises(ValueError):
        protocol.decode_frame_data(GOLDEN_FRAME[:-5])


# --- NT client ----------------------------------------------------------------


class _FakeHeadset:
    """Publishes on the topics a real headset would, in the same NT instance."""

    def __init__(self, inst: NetworkTableInstance) -> None:
        table = inst.get_table("QuestNav")
        opts = PubSubOptions(send_all=True)
        self.frame = table.get_raw_topic("frameData").publish(
            protocol.FRAME_DATA_TYPE, opts
        )
        self.device = table.get_raw_topic("deviceData").publish(
            protocol.DEVICE_DATA_TYPE
        )
        self.response = table.get_raw_topic("response").publish(
            protocol.COMMAND_RESPONSE_TYPE, opts
        )
        self.version = table.get_string_topic("version").publish()
        self.requests = table.get_raw_topic("request").subscribe(
            protocol.COMMAND_TYPE, b"", PubSubOptions(send_all=True)
        )


@pytest.fixture
def nt():
    inst = NetworkTableInstance.create()
    yield inst
    NetworkTableInstance.destroy(inst)


def test_client_reads_every_frame_in_order(nt: NetworkTableInstance) -> None:
    quest = QuestNav(instance=nt)
    headset = _FakeHeadset(nt)
    assert not quest.is_connected()

    for i in range(3):
        headset.frame.set(_frame_bytes(Pose3d(i, 0, 0, Rotation3d()), frame_count=i))
    headset.device.set(GOLDEN_DEVICE)

    frames = quest.get_all_unread_pose_frames()
    assert [f.frame_count for f in frames] == [0, 1, 2]
    assert [f.quest_pose.x for f in frames] == [0.0, 1.0, 2.0]
    # Timestamps are robot-clock seconds (2027 ntcore is nanoseconds internally).
    assert frames[-1].data_timestamp == pytest.approx(
        wpilib.Timer.get_timestamp(), abs=1.0
    )
    assert quest.get_all_unread_pose_frames() == []  # queue consumed
    assert quest.is_connected() and quest.is_tracking()
    assert quest.get_frame_count() == 2
    assert quest.get_battery_percent() == 87
    assert quest.get_tracking_lost_counter() == 3


def test_client_sends_pose_reset_and_reads_response(nt: NetworkTableInstance) -> None:
    quest = QuestNav(instance=nt)
    headset = _FakeHeadset(nt)

    command_id = quest.set_pose(Pose3d(Translation3d(3.0, 4.0, 0.25), Rotation3d()))
    sent = headset.requests.read_queue()
    assert command_id == 1
    assert [r.value for r in sent] == [
        protocol.encode_pose_reset_command(
            1, Pose3d(Translation3d(3.0, 4.0, 0.25), Rotation3d())
        )
    ]

    headset.response.set(GOLDEN_RESPONSE)
    quest.command_periodic()  # reports the failure; must not raise
    assert quest.get_last_command_response() == protocol.CommandResponse(
        7, False, "nope"
    )


# --- Fusion -------------------------------------------------------------------


class _RecordingDrivetrain:
    def __init__(self) -> None:
        self.measurements: list[tuple[Pose2d, float, tuple[float, float, float]]] = []

    def add_vision_measurement(self, pose, timestamp_s, std_devs) -> None:
        self.measurements.append((pose, timestamp_s, std_devs))


def test_subsystem_fuses_robot_pose_through_mount_offset(
    nt: NetworkTableInstance,
) -> None:
    drivetrain = _RecordingDrivetrain()
    subsystem = QuestNavSubsystem(drivetrain, QuestNav(instance=nt))  # type: ignore[arg-type]
    headset = _FakeHeadset(nt)

    robot_pose = Pose2d(4.0, 2.0, Rotation2d.from_degrees(90))
    quest_pose = Pose3d(robot_pose).transform_by(QuestNavConstants.ROBOT_TO_QUEST)
    headset.frame.set(_frame_bytes(quest_pose, frame_count=1))
    headset.frame.set(_frame_bytes(quest_pose, frame_count=2, tracking=False))

    subsystem.periodic()

    assert len(drivetrain.measurements) == 1  # the non-tracking frame is skipped
    fused, _, std_devs = drivetrain.measurements[0]
    assert (fused.x, fused.y) == pytest.approx((4.0, 2.0), abs=1e-9)
    assert fused.rotation().radians() == pytest.approx(math.pi / 2)
    assert std_devs == QuestNavConstants.STD_DEVS


def test_reset_pose_sends_headset_pose(nt: NetworkTableInstance) -> None:
    subsystem = QuestNavSubsystem(_RecordingDrivetrain(), QuestNav(instance=nt))  # type: ignore[arg-type]
    headset = _FakeHeadset(nt)

    robot_pose = Pose2d(1.0, 1.0, Rotation2d.from_degrees(180))
    subsystem.reset_pose(robot_pose)

    [request] = headset.requests.read_queue()
    expected = Pose3d(robot_pose).transform_by(QuestNavConstants.ROBOT_TO_QUEST)
    assert request.value == protocol.encode_pose_reset_command(1, expected)
    # Mount is 0.3 m forward; the robot faces -x, so the headset sits at x = 0.7.
    assert expected.x == pytest.approx(0.7)
