import logging
import threading
import time
from typing import Optional, Callable
from queue import Queue

# FIX: Import the APP_ROOT_LOGGER_NAME constant to make it available in this module's scope.
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

# FIX: Keep the robust try...except block. With the NameError fixed, this will now
# gracefully handle the case where win32hooks cannot be imported.
try:
    from pywinauto import win32hooks
except ImportError:
    win32hooks = None
    # This line will no longer crash because APP_ROOT_LOGGER_NAME is now imported.
    logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.perception.perception_engine").warning("pywinauto.win32hooks could not be imported. OS event perception will be disabled.")

from pywinauto.win32functions import GetWindowText

from mark_i.engines.capture_engine import CaptureEngine


logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.perception.perception_engine")

_observed_windows = set()


def _win_event_callback(event):
    """
    pywinauto event callback. This function runs in the event hook's thread.
    It should be lightweight and simply put data onto the queue.
    """
    global _observed_windows

    hwnd = event.hwnd
    if event.event_name in ["EVENT_SYSTEM_FOREGROUND", "EVENT_OBJECT_CREATE"]:
        try:
            if hwnd in _observed_windows:
                return

            window_text = GetWindowText(hwnd)
            if window_text:
                _observed_windows.add(hwnd)

                perception_event = {"type": "OS_EVENT", "timestamp": time.time(), "data": {"event_type": "NEW_WINDOW_DETECTED", "window_title": window_text, "window_handle": hwnd}}

                PerceptionEngine.get_instance().perception_queue.put(perception_event)
                logger.debug(f"OS Event Hook: Detected new window '{window_text}'")

        except Exception as e:
            logger.warning(f"Error in pywinauto event callback: {e}")


class PerceptionEngine:
    """
    The AI's sensory cortex. Runs in the background to continuously gather
    multi-modal information about the user's environment.
    """

    _instance = None

    def __init__(self, capture_engine: CaptureEngine):
        if PerceptionEngine._instance is not None:
            raise Exception("PerceptionEngine is a singleton and has already been instantiated.")

        self.capture_engine = capture_engine
        self.is_running = False

        self.perception_queue = Queue()

        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

        self.video_fps = 1.0
        self.event_callback_handle = _win_event_callback
        PerceptionEngine._instance = self

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise RuntimeError("PerceptionEngine has not been initialized.")
        return cls._instance

    def start(self):
        if self.is_running:
            logger.warning("PerceptionEngine is already running.")
            return

        self.is_running = True
        self._stop_event.clear()

        video_thread = threading.Thread(target=self._video_loop, daemon=True, name="Perception_Video")
        self._threads.append(video_thread)

        if win32hooks:
            os_events_thread = threading.Thread(target=self._os_events_loop, daemon=True, name="Perception_OS_Events")
            self._threads.append(os_events_thread)
        else:
            logger.warning("OS Event perception thread not started due to missing pywinauto.win32hooks.")

        audio_thread = threading.Thread(target=self._audio_loop, daemon=True, name="Perception_Audio")
        self._threads.append(audio_thread)

        for t in self._threads:
            t.start()

        logger.info(f"PerceptionEngine started with {len(self._threads)} sensory threads.")

    def stop(self):
        if not self.is_running:
            return

        logger.info("Stopping PerceptionEngine...")
        self._stop_event.set()

        if win32hooks:
            try:
                win32hooks.unsubscribe(self.event_callback_handle)
                logger.info("Successfully unsubscribed from Windows OS events.")
            except Exception as e:
                logger.error(f"Error unsubscribing from OS event hook: {e}")

        for t in self._threads:
            t.join(timeout=2.0)

        self.is_running = False
        self._threads.clear()
        logger.info("PerceptionEngine stopped.")

    def _video_loop(self):
        logger.info("Video perception loop started.")
        while not self._stop_event.is_set():
            start_time = time.time()

            screenshot = self.capture_engine.capture_region(
                {"name": "perception_video_frame", "x": 0, "y": 0, "width": self.capture_engine.get_primary_screen_width(), "height": self.capture_engine.get_primary_screen_height()}
            )

            if screenshot is not None:
                perception_event = {"type": "VISUAL_UPDATE", "timestamp": time.time(), "data": screenshot}
                self.perception_queue.put(perception_event)

            elapsed = time.time() - start_time
            sleep_time = (1.0 / self.video_fps) - elapsed
            if sleep_time > 0:
                self._stop_event.wait(timeout=sleep_time)
        logger.info("Video perception loop stopped.")

    def _os_events_loop(self):
        logger.info("OS event perception loop started.")
        global _observed_windows
        _observed_windows.clear()

        try:
            win32hooks.subscribe(self.event_callback_handle)
            logger.info("Successfully subscribed to Windows OS events.")

            while not self._stop_event.is_set():
                time.sleep(30)
                if not self._stop_event.is_set():
                    logger.debug("Clearing observed windows cache.")
                    _observed_windows.clear()

        except Exception as e:
            logger.error(f"Failed to initialize OS event hook: {e}", exc_info=True)
        finally:
            logger.info("OS event perception loop stopped.")

    def _audio_loop(self):
        logger.info("Audio perception loop started (placeholder).")
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=1.0)
        logger.info("Audio perception loop stopped (placeholder).")
