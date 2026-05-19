"""
Decision-making logic.
"""

import math

from pymavlink import mavutil

from ..common.modules.logger import logger
from ..telemetry import telemetry


class Position:
    """
    3D vector struct.
    """

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Command:  # pylint: disable=too-many-instance-attributes
    """
    Command class to make a decision based on recieved telemetry,
    and send out commands based upon the data.
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> "Command":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        return cls(cls.__private_key, connection, target, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.target = target
        self.local_logger = local_logger

        # for average velocity calculation
        self.total_vx = 0.0
        self.total_vy = 0.0
        self.total_vz = 0.0
        self.count = 0

    def run(self, data: telemetry.TelemetryData) -> "list[str]":
        """
        Make a decision based on received telemetry data.
        """
        # Log average velocity for this trip so far
        self.count += 1
        self.total_vx += data.x_velocity
        self.total_vy += data.y_velocity
        self.total_vz += data.z_velocity

        avg_vx = self.total_vx / self.count
        avg_vy = self.total_vy / self.count
        avg_vz = self.total_vz / self.count

        self.local_logger.info(f"Average velocity: ({avg_vx}, {avg_vy}, {avg_vz}) m/s")

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        result = []  # list of strings to return to main

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"
        delta_z = self.target.z - data.z
        target_angle = math.atan2(self.target.y - data.y, self.target.x - data.x)
        delta_yaw = target_angle - data.yaw
        delta_yaw = ((delta_yaw + math.pi) % (2 * math.pi)) - math.pi
        delta_yaw_degrees = math.degrees(delta_yaw)

        if abs(delta_z) > 0.5:
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                0,
                1.0,
                0,
                0,
                0,
                0,
                0,
                self.target.z,
            )
            result.append(f"CHANGE ALTITUDE: {delta_z}")
        elif abs(delta_yaw_degrees) > 5:
            direction = -1 if delta_yaw_degrees > 0 else 1
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                abs(delta_yaw_degrees),
                5,
                direction,
                1,
                0,
                0,
                0,
            )
            result.append(f"CHANGE YAW: {delta_yaw_degrees}")

        return result


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
