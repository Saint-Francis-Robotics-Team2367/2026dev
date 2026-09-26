"""A single swerve module: Phoenix 6 TalonFX drive + steer, CANcoder absolute steer angle.

Control runs on the motor controllers: the drive Talon closes a velocity loop
(``VelocityVoltage``) in wheel rotations, the steer Talon closes a position loop
(``PositionVoltage``) on the CANcoder (``REMOTE_CANCODER``, no Phoenix Pro license
needed) in module rotations with continuous wrap. This class only converts between
WPILib units (meters, radians) and those mechanism rotations.

In simulation, Phoenix simulates the Talons/CANcoder themselves (their firmware and
closed loops); ``simulate()`` supplies the physics — two ``DCMotorSim`` models driven
by the Talons' output voltage — and writes the resulting rotor/encoder readings back
through the devices' ``sim_state``. Note Phoenix's simulated devices run on wall-clock
time, so module behavior is only faithful when the sim runs in real time
(``robotpy sim``); see ``tests/test_swervemodule_sim.py``.

WPILib itself is only imported for simulation. With just ``wpimath`` installed, Phoenix
talks to real hardware, which lets ``bench/module_test.py`` drive this exact class on
the real modules from a laptop + CANivore (importing WPILib would switch Phoenix to
simulated devices).
"""

import math

from phoenix6 import (
    BaseStatusSignal,
    CANBus,
    configs,
    controls,
    hardware,
    signals,
    utils,
)
from phoenix6.sim import ChassisReference
from wpimath import (
    DCMotor,
    Models,
    Rotation2d,
    SwerveModulePosition,
    SwerveModuleVelocity,
)

from constants import ModuleConstants as MC


def _inverted(clockwise_positive: bool) -> signals.InvertedValue:
    if clockwise_positive:
        return signals.InvertedValue.CLOCKWISE_POSITIVE
    return signals.InvertedValue.COUNTER_CLOCKWISE_POSITIVE


class SwerveModule:
    def __init__(
        self,
        name: str,
        drive_id: int,
        steer_id: int,
        encoder_id: int,
        encoder_offset_rot: float = 0.0,
        can_bus: str = "",
        drive_inverted: bool = False,
    ) -> None:
        self.name = name
        bus = CANBus(can_bus)
        self._drive = hardware.TalonFX(drive_id, bus)
        self._steer = hardware.TalonFX(steer_id, bus)
        self._encoder = hardware.CANcoder(encoder_id, bus)

        encoder_cfg = configs.CANcoderConfiguration()
        encoder_cfg.magnet_sensor.magnet_offset = encoder_offset_rot
        # Report -0.5..0.5 rotations, i.e. -180..180 degrees like Rotation2d.
        encoder_cfg.magnet_sensor.absolute_sensor_discontinuity_point = 0.5
        self._encoder.configurator.apply(encoder_cfg)

        drive_cfg = configs.TalonFXConfiguration()
        drive_cfg.motor_output.inverted = _inverted(drive_inverted)
        drive_cfg.motor_output.neutral_mode = signals.NeutralModeValue.BRAKE
        drive_cfg.feedback.sensor_to_mechanism_ratio = MC.DRIVE_GEAR_RATIO
        drive_cfg.slot0.k_s = MC.DRIVE_KS
        drive_cfg.slot0.k_v = MC.DRIVE_KV
        drive_cfg.slot0.k_p = MC.DRIVE_KP
        drive_cfg.current_limits.stator_current_limit = MC.DRIVE_STATOR_LIMIT_A
        drive_cfg.current_limits.stator_current_limit_enable = True
        drive_cfg.current_limits.supply_current_limit = MC.DRIVE_SUPPLY_LIMIT_A
        drive_cfg.current_limits.supply_current_limit_enable = True
        self._drive.configurator.apply(drive_cfg)
        self._drive.set_position(0)

        steer_cfg = configs.TalonFXConfiguration()
        steer_cfg.motor_output.inverted = _inverted(MC.STEER_INVERTED)
        steer_cfg.motor_output.neutral_mode = signals.NeutralModeValue.BRAKE
        steer_cfg.feedback.feedback_sensor_source = (
            signals.FeedbackSensorSourceValue.REMOTE_CANCODER
        )
        steer_cfg.feedback.feedback_remote_sensor_id = encoder_id
        steer_cfg.feedback.rotor_to_sensor_ratio = MC.TURN_GEAR_RATIO
        steer_cfg.feedback.sensor_to_mechanism_ratio = 1.0
        steer_cfg.closed_loop_general.continuous_wrap = True
        steer_cfg.slot0.k_p = MC.STEER_KP
        steer_cfg.slot0.k_d = MC.STEER_KD
        steer_cfg.current_limits.stator_current_limit = MC.STEER_STATOR_LIMIT_A
        steer_cfg.current_limits.stator_current_limit_enable = True
        steer_cfg.current_limits.supply_current_limit = MC.STEER_SUPPLY_LIMIT_A
        steer_cfg.current_limits.supply_current_limit_enable = True
        self._steer.configurator.apply(steer_cfg)

        self._drive_position = self._drive.get_position()
        self._drive_velocity = self._drive.get_velocity()
        self._steer_position = self._steer.get_position()
        self._signals: list[BaseStatusSignal] = [
            self._drive_position,
            self._drive_velocity,
            self._steer_position,
        ]

        self._drive_request = controls.VelocityVoltage(0, enable_foc=MC.USE_FOC)
        self._steer_request = controls.PositionVoltage(0, enable_foc=MC.USE_FOC)

        if utils.is_simulation():
            self._init_sim(encoder_offset_rot, drive_inverted)

    # --- Interface used by Drivetrain / kinematics (units: m, m/s, rad) ---

    def get_state(self) -> SwerveModuleVelocity:
        """Current wheel velocity + angle (for forward kinematics / logging)."""
        BaseStatusSignal.refresh_all(self._signals)
        return SwerveModuleVelocity(
            self._drive_velocity.value * MC.WHEEL_CIRCUMFERENCE_M, self._angle()
        )

    def get_position(self) -> SwerveModulePosition:
        """Accumulated wheel distance + angle (for odometry)."""
        BaseStatusSignal.refresh_all(self._signals)
        return SwerveModulePosition(
            self._drive_position.value * MC.WHEEL_CIRCUMFERENCE_M, self._angle()
        )

    def set_desired_state(self, desired: SwerveModuleVelocity) -> None:
        """Command a new state, taking the shortest path to the target angle."""
        self._steer_position.refresh()
        current = self._angle()
        # Never turn more than 90 deg (reverse the wheel instead), and slow the
        # wheel while the module is still pointed away from the target.
        optimized = desired.optimize(current).cosine_scale(current)
        self._drive.set_control(
            self._drive_request.with_velocity(
                optimized.velocity / MC.WHEEL_CIRCUMFERENCE_M
            )
        )
        self._steer.set_control(
            self._steer_request.with_position(optimized.angle.radians() / math.tau)
        )

    def _angle(self) -> Rotation2d:
        # Uses the value from the latest refresh; callers refresh first.
        return Rotation2d(self._steer_position.value * math.tau)

    # --- Simulation physics ---

    def _init_sim(self, encoder_offset_rot: float, drive_inverted: bool) -> None:
        # Imported here, not at module level: see the module docstring.
        from wpilib import RobotController
        from wpilib.simulation import DCMotorSim

        self._battery_voltage = RobotController.get_battery_voltage
        motor = DCMotor.kraken_x60(1)
        self._drive_sim = DCMotorSim(
            Models.single_jointed_arm_from_physical_constants(
                motor, MC.DRIVE_SIM_MOI, MC.DRIVE_GEAR_RATIO
            ),
            motor,
        )
        self._steer_sim = DCMotorSim(
            Models.single_jointed_arm_from_physical_constants(
                motor, MC.STEER_SIM_MOI, MC.TURN_GEAR_RATIO
            ),
            motor,
        )
        # Sim states report physics in the motor's own frame; match the inversions
        # so a positive mechanism motion reads positive, as on the real robot.
        for talon, clockwise in (
            (self._drive, drive_inverted),
            (self._steer, MC.STEER_INVERTED),
        ):
            talon.sim_state.set_motor_type(talon.sim_state.MotorType.KRAKEN_X60)
            talon.sim_state.orientation = (
                ChassisReference.CLOCKWISE_POSITIVE
                if clockwise
                else ChassisReference.COUNTER_CLOCKWISE_POSITIVE
            )
        self._encoder_offset_rot = encoder_offset_rot

    def simulate(self, dt_s: float) -> None:
        """Advance the motor physics one step and feed the results to the devices."""
        battery = self._battery_voltage()
        drive, steer, encoder = (
            self._drive.sim_state,
            self._steer.sim_state,
            self._encoder.sim_state,
        )
        for s in (drive, steer, encoder):
            s.set_supply_voltage(battery)

        self._drive_sim.set_input_voltage(drive.motor_voltage)
        self._drive_sim.update(dt_s)
        self._steer_sim.set_input_voltage(steer.motor_voltage)
        self._steer_sim.update(dt_s)

        wheel_rot = self._drive_sim.get_angular_position() / math.tau
        wheel_rps = self._drive_sim.get_angular_velocity() / math.tau
        drive.set_raw_rotor_position(wheel_rot * MC.DRIVE_GEAR_RATIO)
        drive.set_rotor_velocity(wheel_rps * MC.DRIVE_GEAR_RATIO)

        module_rot = self._steer_sim.get_angular_position() / math.tau
        module_rps = self._steer_sim.get_angular_velocity() / math.tau
        steer.set_raw_rotor_position(module_rot * MC.TURN_GEAR_RATIO)
        steer.set_rotor_velocity(module_rps * MC.TURN_GEAR_RATIO)
        # The CANcoder adds its magnet offset to the raw reading; remove it here so
        # the simulated module reads the true physical angle.
        encoder.set_raw_position(module_rot - self._encoder_offset_rot)
        encoder.set_velocity(module_rps)
