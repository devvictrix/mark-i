import logging
from queue import Queue
from typing import Any


class GuiLoggingHandler(logging.Handler):
    """
    A custom logging handler that puts formatted log records into a queue.
    This allows a background thread (like the bot runner) to safely send log
    messages to the main GUI thread for display.
    """

    def __init__(self, log_queue: Queue[Any]):
        """
        Initializes the handler.

        Args:
            log_queue: A thread-safe queue.Queue instance.
        """
        super().__init__()
        self.log_queue = log_queue
        # Set a simple formatter. The log level will be determined by the logger this
        # handler is attached to.
        self.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord):
        """
        Formats the log record and puts the message into the queue.
        This method is thread-safe because queue.Queue is thread-safe.
        """
        msg = self.format(record)
        self.log_queue.put(msg)
