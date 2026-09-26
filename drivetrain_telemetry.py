"""Publishes drivetrain telemetry to NetworkTables for dashboards.

Everything here is visible in Elastic (connect to ``localhost`` in simulation),
AdvantageScope, and the WPILib Simulation GUI. Struct topics use the WPILib
serialization schema, so no manual encoding is needed — the pose, chassis
velocities, and module states go out as first-class typed values.
"""

import math
from collections.abc import Sequence

from ntcore import NetworkTableInstance
from wpimath import ChassisVelocities, Pose2d, SwerveModuleVelocity


class DrivetrainTelemetry:
    """Owns the NetworkTables publishers for the drivetrain."""

    def __init__(self, table_name: str = "Drivetrain") -> None:
        table = NetworkTableInstance.get_default().get_table(table_name)
        # Publishers must be retained (they unpublish when garbage-collected).
        self._pose = table.get_struct_topic("pose", Pose2d).publish()
        self._chassis = table.get_struct_topic(
            "chassisVelocities", ChassisVelocities
        ).publish()
        self._states = table.get_struct_array_topic(
            "moduleStates", SwerveModuleVelocity
        ).publish()
        self._heading_deg = table.get_double_topic("headingDegrees").publish()
        self._speed_mps = table.get_double_topic("speedMps").publish()

    def publish(
        self,
        pose: Pose2d,
        chassis: ChassisVelocities,
        module_states: Sequence[SwerveModuleVelocity],
    ) -> None:
        self._pose.set(pose)
        self._chassis.set(chassis)
        self._states.set(list(module_states))
        self._heading_deg.set(pose.rotation().degrees())
        self._speed_mps.set(math.hypot(chassis.vx, chassis.vy))
