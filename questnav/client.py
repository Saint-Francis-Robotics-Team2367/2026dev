"""NetworkTables client for a QuestNav headset — a Python port of QuestNavLib.

Mirrors the Java ``gg.questnav.questnav.QuestNav`` class: it subscribes to the
headset's ``QuestNav/*`` topics, hands back unread pose frames for the pose
estimator, and sends pose-reset commands. Call ``command_periodic()`` and
``get_all_unread_pose_frames()`` once per robot loop.

Time bases: 2027 ntcore timestamps are **nanoseconds** (2026 was microseconds),
in the same clock as ``wpilib.Timer.get_timestamp()`` on the robot, so frame
timestamps can go straight into ``add_vision_measurement``.
"""

from collections.abc import Callable
from dataclasses import dataclass

import wpilib
from ntcore import NetworkTableInstance, PubSubOptions, TimestampedRaw
from wpimath import Pose3d

from questnav import protocol
from questnav.protocol import CommandResponse, DeviceData, FrameData

_NS_PER_S = 1e9
# A frame newer than this means the headset is connected (frames arrive at 100 Hz).
_CONNECTED_TIMEOUT_S = 0.12
_VERSION_CHECK_INTERVAL_S = 5.0


@dataclass(frozen=True)
class PoseFrame:
    """One tracking frame, timestamped in robot time."""

    # The headset's field pose; transform by the mounting offset for the robot's.
    quest_pose: Pose3d
    # When the frame was published, in ``wpilib.Timer.get_timestamp()`` seconds.
    data_timestamp: float
    # Seconds since the QuestNav app started (headset clock).
    app_timestamp: float
    frame_count: int
    is_tracking: bool


class QuestNav:
    """Reads pose/device data from a QuestNav headset and sends it commands."""

    def __init__(
        self,
        expected_version: str | None = None,
        instance: NetworkTableInstance | None = None,
        table_name: str = "QuestNav",
    ) -> None:
        """``expected_version`` is the headset app version this code was written
        against; a mismatch logs a periodic warning. ``None`` disables the check."""
        table = (instance or NetworkTableInstance.get_default()).get_table(table_name)
        self._expected_version = expected_version
        # Subscribe options match QuestNavLib: every frame is kept (send_all) so
        # none are lost between robot loops.
        self._frame_sub = table.get_raw_topic("frameData").subscribe(
            protocol.FRAME_DATA_TYPE,
            b"",
            PubSubOptions(periodic=0.01, send_all=True, poll_storage=20),
        )
        self._device_sub = table.get_raw_topic("deviceData").subscribe(
            protocol.DEVICE_DATA_TYPE, b""
        )
        self._response_sub = table.get_raw_topic("response").subscribe(
            protocol.COMMAND_RESPONSE_TYPE,
            b"",
            PubSubOptions(periodic=0.05, send_all=True, poll_storage=20),
        )
        self._version_sub = table.get_string_topic("version").subscribe("unknown")
        self._request_pub = table.get_raw_topic("request").publish(
            protocol.COMMAND_TYPE
        )
        self._last_command_id = 0
        self._last_version_check_s = -_VERSION_CHECK_INTERVAL_S
        self._last_response: CommandResponse | None = None

    # --- Per-loop calls -----------------------------------------------------

    def get_all_unread_pose_frames(self) -> list[PoseFrame]:
        """Every frame received since the last call (consumes the queue)."""
        frames = []
        for raw in self._frame_sub.read_queue():
            data = _decode(protocol.decode_frame_data, raw.value)
            if data is None:
                continue
            frames.append(
                PoseFrame(
                    data.quest_pose,
                    _timestamp_s(raw),
                    data.app_timestamp,
                    data.frame_count,
                    data.is_tracking,
                )
            )
        return frames

    def command_periodic(self) -> None:
        """Report command failures and warn on an app/code version mismatch."""
        for raw in self._response_sub.read_queue():
            response = _decode(protocol.decode_command_response, raw.value)
            if response is None:
                continue
            self._last_response = response
            if not response.success:
                wpilib.report_error(
                    f"QuestNav command {response.command_id} failed: "
                    f"{response.error_message}",
                    False,
                )
        self._check_version()

    def set_pose(self, quest_pose: Pose3d) -> int:
        """Reset the headset's origin so it reports ``quest_pose`` right now.

        This is the *headset's* pose: transform the robot pose by the mounting
        offset first. Returns the command ID echoed back in the response.
        """
        self._last_command_id = (self._last_command_id + 1) & 0xFFFFFFFF
        self._request_pub.set(
            protocol.encode_pose_reset_command(self._last_command_id, quest_pose)
        )
        return self._last_command_id

    # --- Status -------------------------------------------------------------

    def get_latency_s(self) -> float:
        """Seconds since the last frame arrived."""
        last_change_s = self._frame_sub.get_last_change() / _NS_PER_S
        return wpilib.Timer.get_timestamp() - last_change_s

    def is_connected(self) -> bool:
        return (
            self._frame_sub.get_last_change() != 0
            and self.get_latency_s() < _CONNECTED_TIMEOUT_S
        )

    def is_tracking(self) -> bool:
        frame = self._latest_frame()
        return frame is not None and frame.is_tracking

    def get_frame_count(self) -> int | None:
        frame = self._latest_frame()
        return frame.frame_count if frame is not None else None

    def get_app_timestamp(self) -> float | None:
        frame = self._latest_frame()
        return frame.app_timestamp if frame is not None else None

    def get_battery_percent(self) -> int | None:
        device = self._latest_device()
        return device.battery_percent if device is not None else None

    def get_tracking_lost_counter(self) -> int | None:
        device = self._latest_device()
        return device.tracking_lost_counter if device is not None else None

    def get_last_command_response(self) -> CommandResponse | None:
        return self._last_response

    def get_questnav_version(self) -> str:
        return self._version_sub.get()

    # --- Internals ----------------------------------------------------------

    def _latest_frame(self) -> FrameData | None:
        raw = self._frame_sub.get()
        return _decode(protocol.decode_frame_data, raw) if raw else None

    def _latest_device(self) -> DeviceData | None:
        raw = self._device_sub.get()
        return _decode(protocol.decode_device_data, raw) if raw else None

    def _check_version(self) -> None:
        if self._expected_version is None or not self.is_connected():
            return
        now = wpilib.Timer.get_timestamp()
        if now - self._last_version_check_s < _VERSION_CHECK_INTERVAL_S:
            return
        self._last_version_check_s = now
        version = self.get_questnav_version()
        if version != self._expected_version:
            wpilib.report_warning(
                f"QuestNav app version on the headset ({version}) does not match "
                f"the version this robot code expects ({self._expected_version})."
            )


def _timestamp_s(raw: TimestampedRaw) -> float:
    # server_time is 0/1 for values published locally (tests, or a sim fake);
    # fall back to the local receive time, which is the same clock on the server.
    time_ns = raw.server_time if raw.server_time > 1 else raw.time
    return time_ns / _NS_PER_S


def _decode[T](decoder: Callable[[bytes], T], buf: bytes) -> T | None:
    try:
        return decoder(buf)
    except ValueError:
        wpilib.report_warning("QuestNav: dropped a malformed message")
        return None
