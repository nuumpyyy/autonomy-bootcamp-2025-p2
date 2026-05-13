"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib
import time

from pymavlink import mavutil

from utilities.workers import worker_controller
from . import heartbeat_sender
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def heartbeat_sender_worker(
    connection: mavutil.mavfile, controller: worker_controller.WorkerController
) -> None:
    """
    Worker process.

    connection is the MAVLink connection for communication between workers.
    controller is how the main process communicates to this worker process.
    """
    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    # Instantiate logger
    worker_name = pathlib.Path(__file__).stem
    process_id = os.getpid()
    result, local_logger = logger.Logger.create(f"{worker_name}_{process_id}", True)
    if not result:
        print("ERROR: Worker failed to create logger")
        return

    # Get Pylance to stop complaining
    assert local_logger is not None

    local_logger.info("Logger initialized", True)

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Instantiate class object (heartbeat_sender.HeartbeatSender)
    ret, heartbeat_sender_instance = heartbeat_sender.HeartbeatSender.create(
        connection, local_logger
    )

    if not ret:
        local_logger.error("Failed to instantiate HeartbeatSender object", True)
        return

    # Main loop: do work.
    while not controller.is_exit_requested():
        # block worker if pause has been requested
        controller.check_pause()

        start = time.time()
        result = heartbeat_sender_instance.run()
        elapsed = time.time() - start
        local_logger.info("Heartbeat sent")

        time.sleep(max(0, 1 - elapsed))  # in case result takes longer than 1 second to run


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
