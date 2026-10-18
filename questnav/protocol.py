"""Minimal protobuf codec for the QuestNav NetworkTables messages.

QuestNav ships only a Java vendor library, so this module speaks its wire format
directly. The messages are tiny and stable (see ``protos/`` in the QuestNav repo:
``data.proto``, ``commands.proto``, ``geometry3d.proto``), so a hand-written
proto3 codec avoids a ``protobuf`` runtime dependency and a codegen step on the
robot. ``tests/test_questnav.py`` checks it against bytes produced by the official
protobuf compiler.

Only the fields robot code needs are modeled; unknown fields are skipped, so newer
headset builds that add fields (e.g. ``server_timestamp``) still decode.
"""

import struct
from collections.abc import Iterator
from dataclasses import dataclass
from typing import NamedTuple

from wpimath import Pose3d, Quaternion, Rotation3d, Translation3d

# NT4 type strings the headset uses: "proto:" + the message's full proto name.
FRAME_DATA_TYPE = "proto:questnav.protos.data.ProtobufQuestNavFrameData"
DEVICE_DATA_TYPE = "proto:questnav.protos.data.ProtobufQuestNavDeviceData"
COMMAND_TYPE = "proto:questnav.protos.commands.ProtobufQuestNavCommand"
COMMAND_RESPONSE_TYPE = "proto:questnav.protos.commands.ProtobufQuestNavCommandResponse"

# questnav.protos.commands.QuestNavCommandType
POSE_RESET = 1

_VARINT = 0
_FIXED64 = 1
_LENGTH = 2
_FIXED32 = 5


@dataclass(frozen=True)
class FrameData:
    """One high-rate (100 Hz) tracking frame from the headset."""

    frame_count: int
    # Seconds since the QuestNav app started (headset clock, not robot time).
    app_timestamp: float
    # The *headset's* field pose; apply the mounting transform to get the robot's.
    quest_pose: Pose3d
    is_tracking: bool


@dataclass(frozen=True)
class DeviceData:
    """Low-rate (3 Hz) headset status."""

    tracking_lost_counter: int
    battery_percent: int


@dataclass(frozen=True)
class CommandResponse:
    command_id: int
    success: bool
    error_message: str


# --- Wire-format primitives -------------------------------------------------


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        if pos >= len(buf):
            raise ValueError("truncated varint")
        byte = buf[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7
        if shift >= 64:
            raise ValueError("varint too long")


def _to_int32(value: int) -> int:
    """Reinterpret a decoded varint as a signed int32 (negatives are 10 bytes)."""
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


class _Field(NamedTuple):
    number: int
    wire: int
    varint: int  # set for VARINT fields, else 0
    data: bytes  # raw payload for FIXED64 / LENGTH / FIXED32 fields, else b""


def _fields(buf: bytes) -> Iterator[_Field]:
    pos = 0
    while pos < len(buf):
        key, pos = _read_varint(buf, pos)
        number, wire = key >> 3, key & 0x7
        varint, data = 0, b""
        if wire == _VARINT:
            varint, pos = _read_varint(buf, pos)
        elif wire == _FIXED64:
            data, pos = buf[pos : pos + 8], pos + 8
        elif wire == _LENGTH:
            length, pos = _read_varint(buf, pos)
            data, pos = buf[pos : pos + length], pos + length
        elif wire == _FIXED32:
            data, pos = buf[pos : pos + 4], pos + 4
        else:
            raise ValueError(f"unsupported wire type {wire}")
        if pos > len(buf):
            raise ValueError("truncated field")
        yield _Field(number, wire, varint, data)


def _double(value: bytes) -> float:
    return struct.unpack("<d", value)[0]


def _encode_varint(value: int) -> bytes:
    value &= (1 << 64) - 1
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _key(field: int, wire: int) -> bytes:
    return _encode_varint(field << 3 | wire)


def _encode_double(field: int, value: float) -> bytes:
    # proto3 omits fields at their default value.
    return _key(field, _FIXED64) + struct.pack("<d", value) if value != 0.0 else b""


def _encode_message(field: int, payload: bytes) -> bytes:
    return _key(field, _LENGTH) + _encode_varint(len(payload)) + payload


# --- wpi.proto geometry -----------------------------------------------------


def _decode_translation(buf: bytes) -> Translation3d:
    xyz = [0.0, 0.0, 0.0]
    for field, wire, varint, data in _fields(buf):
        if wire == _FIXED64 and 1 <= field <= 3:
            xyz[field - 1] = _double(data)
    return Translation3d(*xyz)


def _decode_quaternion(buf: bytes) -> Quaternion:
    wxyz = [0.0, 0.0, 0.0, 0.0]
    for field, wire, varint, data in _fields(buf):
        if wire == _FIXED64 and 1 <= field <= 4:
            wxyz[field - 1] = _double(data)
    return Quaternion(*wxyz)


def _decode_rotation(buf: bytes) -> Rotation3d:
    for field, wire, varint, data in _fields(buf):
        if field == 1 and wire == _LENGTH:
            return Rotation3d(_decode_quaternion(data))
    return Rotation3d()


def decode_pose3d(buf: bytes) -> Pose3d:
    translation = Translation3d()
    rotation = Rotation3d()
    for field, wire, varint, data in _fields(buf):
        if wire != _LENGTH:
            continue
        if field == 1:
            translation = _decode_translation(data)
        elif field == 2:
            rotation = _decode_rotation(data)
    return Pose3d(translation, rotation)


def encode_pose3d(pose: Pose3d) -> bytes:
    t = pose.translation()
    q = pose.rotation().get_quaternion()
    translation = (
        _encode_double(1, t.x) + _encode_double(2, t.y) + _encode_double(3, t.z)
    )
    quaternion = (
        _encode_double(1, q.w)
        + _encode_double(2, q.x)
        + _encode_double(3, q.y)
        + _encode_double(4, q.z)
    )
    rotation = _encode_message(1, quaternion)
    return _encode_message(1, translation) + _encode_message(2, rotation)


# --- QuestNav messages ------------------------------------------------------


def decode_frame_data(buf: bytes) -> FrameData:
    frame_count = 0
    app_timestamp = 0.0
    quest_pose = Pose3d()
    is_tracking = False
    for field, wire, varint, data in _fields(buf):
        if field == 1 and wire == _VARINT:
            frame_count = _to_int32(varint)
        elif field == 2 and wire == _FIXED64:
            app_timestamp = _double(data)
        elif field == 3 and wire == _LENGTH:
            quest_pose = decode_pose3d(data)
        elif field == 4 and wire == _VARINT:
            is_tracking = varint != 0
    return FrameData(frame_count, app_timestamp, quest_pose, is_tracking)


def decode_device_data(buf: bytes) -> DeviceData:
    tracking_lost_counter = 0
    battery_percent = 0
    for field, wire, varint, data in _fields(buf):
        if wire != _VARINT:
            continue
        if field == 1:
            tracking_lost_counter = _to_int32(varint)
        elif field == 3:
            battery_percent = _to_int32(varint)
    return DeviceData(tracking_lost_counter, battery_percent)


def decode_command_response(buf: bytes) -> CommandResponse:
    command_id = 0
    success = False
    error_message = ""
    for field, wire, varint, data in _fields(buf):
        if field == 1 and wire == _VARINT:
            command_id = varint & 0xFFFFFFFF
        elif field == 2 and wire == _VARINT:
            success = varint != 0
        elif field == 3 and wire == _LENGTH:
            error_message = data.decode("utf-8", errors="replace")
    return CommandResponse(command_id, success, error_message)


def encode_pose_reset_command(command_id: int, quest_pose: Pose3d) -> bytes:
    """A POSE_RESET request telling the headset its own (not the robot's) pose."""
    payload = _encode_message(1, encode_pose3d(quest_pose))
    return (
        _key(1, _VARINT)
        + _encode_varint(POSE_RESET)
        + _key(2, _VARINT)
        + _encode_varint(command_id & 0xFFFFFFFF)
        + _encode_message(10, payload)
    )
