"""Bring-up command: spin each drive and steer TalonFX in turn, logging to the DS console."""

import time
from dataclasses import dataclass, field
from typing import Any

from commands2 import Command
from phoenix6 import BaseStatusSignal, CANBus, controls, hardware, signals

from constants import DebugConstants, HardwareIds
from dslog import log
from subsystems.drivetrain import Drivetrain

_CORNERS = ("FL", "FR", "BL", "BR")


@dataclass
class _Motor:
    label: str
    can_id: int
    talon: hardware.TalonFX
    signals: list[Any] = field(default_factory=list)
    peak_rps: float = 0.0
    peak_amps: float = 0.0
    enabled: bool = False

    def refresh(self) -> tuple[float, float, float, float, float, object, int]:
        BaseStatusSignal.refresh_all(self.signals, report_error=False)
        pos, vel, volts, amps, supply, enable, faults = (s.value for s in self.signals)
        self.peak_rps = max(self.peak_rps, abs(vel))
        self.peak_amps = max(self.peak_amps, abs(amps))
        self.enabled = self.enabled or enable == signals.RobotEnableValue.ENABLED
        return pos, vel, volts, amps, supply, enable, int(faults)


class SpinAllMotors(Command):
    """Spins every drive and steer motor one at a time with ``VoltageOut``, then logs a summary.

    Requires the drivetrain so the teleop default command can't fight it for the motors.
    Only one motor runs at a time; the rest are neutral.
    """

    def __init__(self, drivetrain: Drivetrain) -> None:
        super().__init__()
        self.add_requirements(drivetrain)
        bus = CANBus(HardwareIds.CAN_BUS)
        self._motors: list[_Motor] = []
        for kind, ids in (
            ("drive", HardwareIds.DRIVE_MOTOR_CAN),
            ("steer", HardwareIds.TURN_MOTOR_CAN),
        ):
            for corner, can_id in zip(_CORNERS, ids):
                talon = hardware.TalonFX(can_id, bus)
                motor = _Motor(f"{corner} {kind}", can_id, talon)
                motor.signals = [
                    talon.get_position(),
                    talon.get_velocity(),
                    talon.get_motor_voltage(),
                    talon.get_stator_current(),
                    talon.get_supply_voltage(),
                    talon.get_robot_enable(),
                    talon.get_fault_field(),
                ]
                self._motors.append(motor)
        self._request = controls.VoltageOut(DebugConstants.SPIN_VOLTS)
        self._neutral = controls.NeutralOut()
        self._index = 0
        self._started = 0.0
        self._next_log = 0.0
        self._done = False

    def initialize(self) -> None:
        self._index = 0
        self._done = False
        for m in self._motors:
            m.peak_rps = m.peak_amps = 0.0
            m.enabled = False
        log(
            f"[spin] start: {len(self._motors)} motors on bus {HardwareIds.CAN_BUS!r}, "
            f"{DebugConstants.SPIN_VOLTS:+.2f} V for {DebugConstants.SPIN_SECONDS:.1f} s each"
        )
        self._begin_motor()

    def _begin_motor(self) -> None:
        m = self._motors[self._index]
        self._started = self._next_log = time.monotonic()
        log(
            f"[spin] ({self._index + 1}/{len(self._motors)}) {m.label} id={m.can_id} "
            f"connected={m.talon.is_connected}"
        )

    def execute(self) -> None:
        m = self._motors[self._index]
        now = time.monotonic()
        m.talon.set_control(self._request)
        if now >= self._next_log:
            self._next_log = now + DebugConstants.LOG_PERIOD_S
            if not m.talon.is_connected:
                log(f"[spin] {m.label} id={m.can_id} NOT CONNECTED")
            else:
                pos, vel, volts, amps, supply, enable, faults = m.refresh()
                log(
                    f"[spin] {m.label} id={m.can_id} pos={pos:+.3f} rot vel={vel:+.2f} rps "
                    f"out={volts:+.2f} V stator={amps:.1f} A supply={supply:.2f} V "
                    f"enable={enable} faults=0x{faults:x}"
                )
        if now - self._started >= DebugConstants.SPIN_SECONDS:
            m.refresh()
            m.talon.set_control(self._neutral)
            self._index += 1
            if self._index >= len(self._motors):
                self._done = True
            else:
                self._begin_motor()

    def is_finished(self) -> bool:
        return self._done

    def end(self, interrupted: bool) -> None:
        for m in self._motors:
            m.talon.set_control(self._neutral)
        log(f"[spin] stop (interrupted={interrupted})")
        for m in self._motors:
            ok = (
                m.talon.is_connected
                and m.enabled
                and m.peak_rps >= DebugConstants.MIN_SPIN_RPS
            )
            log(
                f"[spin] {'OK  ' if ok else 'FAIL'} {m.label:<8} id={m.can_id:<3} "
                f"peak={m.peak_rps:.2f} rps {m.peak_amps:.1f} A "
                f"connected={m.talon.is_connected} enabled={m.enabled}"
            )
