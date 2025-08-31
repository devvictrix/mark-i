import logging
import threading
import time
from queue import Queue
from typing import Any

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.symbiosis.bci_engine")


class BCIEngine:
    """
    Hardware Abstraction Layer for a conceptual Brain-Computer Interface.
    In this simulation, it generates mock events. In a real implementation,
    it would interface with a hardware SDK.
    """

    def __init__(self):
        self.is_running = False
        self.bci_event_queue = Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        logger.info("BCIEngine initialized (Simulated).")

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._thread.start()
        logger.info("BCIEngine started.")

    def stop(self):
        if not self.is_running:
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self.is_running = False
        logger.info("BCIEngine stopped.")

    def _simulation_loop(self):
        """A loop to simulate incoming BCI events."""
        while not self._stop_event.is_set():
            # Simulate a user having a thought that becomes a command
            if self.bci_event_queue.empty():  # Don't flood the queue
                bci_event = {"type": "THOUGHT_RECEIVED", "data": "What are the primary risks of our current project plan?"}
                self.bci_event_queue.put(bci_event)
            time.sleep(15)  # Simulate new thoughts periodically

    def send_data_to_user(self, data: Any):
        """Simulates sending data back to the user's visual cortex."""
        logger.info(f"[BCI SIMULATION] Projecting data to user's mind's eye: '{str(data)[:100]}...'")
        # In a real implementation, this would call the hardware SDK.
        return True
