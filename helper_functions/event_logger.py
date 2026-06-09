'''
This module provides a structured logging system for the Dobot system.
It writes JSONL files (one JSON line per event) - easy to parse for analysis.
'''

import json
import time
import os
from datetime import datetime
from threading import Lock


class EventLogger:
    '''
    EventLogger is a simple structured logger that writes events to a JSONL file.
    '''
    def __init__(self, component, log_dir="logs", run_id=None):
        '''
        Initializes the EventLogger.

        Args:
            component (str): Name of the component logging events.
            log_dir (str): Directory where log files will be stored.
            run_id (str, optional): Unique ID for the logging session. If None, uses the current date.
        '''
        self.component = component
        os.makedirs(log_dir, exist_ok=True)

        # One log file per day (could be changed to per run if needed).
        if run_id is None:
            run_id = datetime.now().strftime("%Y-%m-%d")
        self.run_id = run_id

        self.log_path = os.path.join(log_dir, f"dobot_log_{run_id}.jsonl")
        self._lock = Lock()  # Thread-safety if multiple threads log to the same file

        # For tracking open actions (start without end)
        self._open_events = {}

        self._write({
            "event": "logger_started",
            "component": component,
        })

    def _write(self, payload):
        '''
        Writes a line to the log file. Always includes a timestamp and component.
        '''
        record = {
            "ts": time.time(),                                    # Unix-Timestamp (for computing durations, sorting, etc.)
            "ts_iso": datetime.now().isoformat(timespec="milliseconds"),  # ISO format
            "component": self.component,
            **payload,
        }
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Simple info and error logging (no duration)
    def info(self, event, **fields):
        '''
        Logs a simple info event without a duration.
        '''
        self._write({"level": "INFO", "event": event, **fields})

    def error(self, event, **fields):
        '''
        Logs a simple error event without a duration.
        '''
        self._write({"level": "ERROR", "event": event, **fields})

    # Actions with start and end (for measuring durations)
    def start(self, action, **fields):
        '''
        Marks the start of an action. 'action' is the unique name,
        e.g., 'move_to_pick', 'gripper_close', 'sorting_blue'.
        '''
        self._open_events[action] = time.time()
        self._write({"level": "INFO", "event": "action_start", "action": action, **fields})

    def end(self, action, **fields):
        ''' 
        Marks the end of an action started with start().
        '''
        start_ts = self._open_events.pop(action, None)
        duration = (time.time() - start_ts) if start_ts else None
        self._write({
            "level": "INFO",
            "event": "action_end",
            "action": action,
            "duration_s": duration,
            **fields,
        })

    # Context manager for timing actions (syntactic sugar)
    def timed(self, action, **fields):
        '''
        Context manager to automatically log start and end of an action, including duration.
        Usage:
            with logger.timed("move_to_pick"):
                dobot.move_to(...)
        '''
        return _TimedAction(self, action, fields)


class _TimedAction:
    def __init__(self, logger, action, fields):
        self.logger = logger
        self.action = action
        self.fields = fields

    def __enter__(self):
        self.logger.start(self.action, **self.fields)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.end(self.action, status="error", error=str(exc_val))
        else:
            self.logger.end(self.action, status="ok")
        return False  # Don't suppress exceptions
