"""A single swerve module — idealized simulation model.

For the 2027 preseason we have no CAN motor vendordeps (Phoenix6 / REVLib) yet
and run simulation-only, so this is a *kinematic* model: the module is assumed to
reach its commanded angle instantly and its commanded wheel velocity perfectly.
That is enough to exercise kinematics, odometry, and Field2d.

When real hardware arrives, keep this interface (``set_desired_state`` /
``get_state`` / ``get_position``) and replace the internals with closed-loop
control on real motors + encoders (and a ``wpilib.simulation`` motor model).
"""

from wpimath import Rotation2d, SwerveModulePosition, SwerveModuleVelocity


class SwerveModule:
    def __init__(self, name: str) -> None:
        self.name = name
        self._angle = Rotation2d()
        self._velocity_mps: float = 0.0
        self._distance_m: float = 0.0

    def get_state(self) -> SwerveModuleVelocity:
        """Current wheel velocity + angle (for forward kinematics / logging)."""
        return SwerveModuleVelocity(self._velocity_mps, self._angle)

    def get_position(self) -> SwerveModulePosition:
        """Accumulated wheel distance + angle (for odometry)."""
        return SwerveModulePosition(self._distance_m, self._angle)

    def set_desired_state(self, desired: SwerveModuleVelocity) -> None:
        """Command a new state, taking the shortest path to the target angle."""
        optimized = desired.optimize(self._angle)
        # Idealized module: it reaches the commanded angle and velocity at once.
        self._angle = optimized.angle
        self._velocity_mps = optimized.velocity

    def simulate(self, dt_s: float) -> None:
        """Advance the simulated wheel distance by one timestep."""
        self._distance_m += self._velocity_mps * dt_s
