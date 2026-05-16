"""
event_logger.py
Strukturiertes Logging für das Dobot-System.
Schreibt JSONL-Dateien (eine JSON-Zeile pro Event) - einfach zu parsen für Auswertungen.
"""

import json
import time
import os
from datetime import datetime
from threading import Lock


class EventLogger:
    def __init__(self, component, log_dir="logs", run_id=None):
        """
        component: Name der Komponente, z.B. "controller", "pickplace", "sorter"
        log_dir:   Ordner in dem die Logs landen
        run_id:    Optional gemeinsame ID für einen Durchlauf (sonst Zeitstempel des Tages)
        """
        self.component = component
        os.makedirs(log_dir, exist_ok=True)

        # Ein Log pro Tag - so landen alle Komponenten desselben Tages in derselben Datei
        # (kann man später beliebig anders machen)
        if run_id is None:
            run_id = datetime.now().strftime("%Y-%m-%d")
        self.run_id = run_id

        self.log_path = os.path.join(log_dir, f"dobot_log_{run_id}.jsonl")
        self._lock = Lock()  # Thread-sicher, falls MQTT-Callbacks parallel feuern

        # Für Dauer-Messungen: Start-Zeitpunkte zwischenspeichern
        self._open_events = {}

        self._write({
            "event": "logger_started",
            "component": component,
        })

    def _write(self, payload):
        """Schreibt eine Zeile in die Logdatei. Immer mit Zeitstempel und Komponente."""
        record = {
            "ts": time.time(),                                    # Unix-Timestamp (für Berechnungen)
            "ts_iso": datetime.now().isoformat(timespec="milliseconds"),  # Lesbar
            "component": self.component,
            **payload,
        }
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # --- Einfache Events (Punkt-Ereignisse) ---
    def info(self, event, **fields):
        """Loggt ein einzelnes Ereignis ohne Dauer."""
        self._write({"level": "INFO", "event": event, **fields})

    def error(self, event, **fields):
        self._write({"level": "ERROR", "event": event, **fields})

    # --- Aktionen mit Dauer (Start + Ende) ---
    def start(self, action, **fields):
        """
        Markiert den Start einer Aktion. 'action' ist der eindeutige Name,
        z.B. 'move_to_pick', 'gripper_close', 'sorting_blue'.
        """
        self._open_events[action] = time.time()
        self._write({"level": "INFO", "event": "action_start", "action": action, **fields})

    def end(self, action, **fields):
        """Markiert das Ende einer mit start() begonnenen Aktion."""
        start_ts = self._open_events.pop(action, None)
        duration = (time.time() - start_ts) if start_ts else None
        self._write({
            "level": "INFO",
            "event": "action_end",
            "action": action,
            "duration_s": duration,
            **fields,
        })

    # --- Context-Manager für ganz bequemes Messen ---
    def timed(self, action, **fields):
        """
        Verwendung:
            with logger.timed("move_to_pick"):
                dobot.move_to(...)
        """
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
        return False  # Exception nicht schlucken
