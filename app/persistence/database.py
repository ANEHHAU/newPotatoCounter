import sqlite3
import json
import threading
import os
import queue
from datetime import datetime
from ..utils.logger import ls

DEFAULT_DB_PATH = "potato_qc.db"

class DatabaseManager:
    """
    SQLite thread-safe logger for sessions and potato events.
    """
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        self.queue = queue.Queue()
        self.running = True
        self.current_session_id = None
        self._init_db()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def _init_db(self):
        """
        Creates schema if not exists.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT,
            ended_at TEXT,
            source TEXT,
            model_path TEXT,
            config_snapshot TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS potato_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            track_id INTEGER,
            final_label TEXT,
            final_confidence REAL,
            decision_reason TEXT,
            frames_in_zone INTEGER,
            counted_at TEXT,
            snapshot BLOB,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS frame_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            timestamp TEXT,
            input_fps REAL,
            processing_fps REAL,
            active_tracks INTEGER,
            belt_speed_px REAL,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
        """)
        
        conn.commit()
        conn.close()

    def start_session(self, source, model_path, config_dict):
        """
        Registers a new session in the database.
        """
        now = datetime.now().isoformat()
        config_snapshot = json.dumps(config_dict)
        
        def task(conn):
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sessions (started_at, source, model_path, config_snapshot)
            VALUES (?, ?, ?, ?)
            """, (now, str(source), str(model_path), config_snapshot))
            conn.commit()
            self.current_session_id = cursor.lastrowid
            ls.info(f"Database session started: ID {self.current_session_id}")

        self.queue.put(task)

    def end_session(self):
        """
        Finalizes the current session.
        """
        if not self.current_session_id:
            return
            
        now = datetime.now().isoformat()
        session_id = self.current_session_id
        
        def task(conn):
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET ended_at = ? WHERE id = ?", (now, session_id))
            conn.commit()
            ls.info(f"Database session ended: ID {session_id}")

        self.queue.put(task)
        self.current_session_id = None

    def log_event(self, track_id, final_label, final_confidence, reason, frames_in_zone, snapshot_bytes=None):
        """
        Logs a single potato event.
        """
        if not self.current_session_id:
            return
            
        session_id = self.current_session_id
        now = datetime.now().isoformat()
        
        def task(conn):
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO potato_events 
            (session_id, track_id, final_label, final_confidence, decision_reason, frames_in_zone, counted_at, snapshot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, track_id, final_label, float(final_confidence), reason, int(frames_in_zone), now, snapshot_bytes))
            conn.commit()

        self.queue.put(task)

    def log_metrics(self, input_fps, proc_fps, n_tracks, speed):
        """
        Logs frame-level performance metrics.
        """
        if not self.current_session_id:
            return
            
        session_id = self.current_session_id
        now = datetime.now().isoformat()
        
        def task(conn):
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO frame_metrics (session_id, timestamp, input_fps, processing_fps, active_tracks, belt_speed_px)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, now, float(input_fps), float(proc_fps), int(n_tracks), float(speed)))
            conn.commit()

        self.queue.put(task)

    def _worker(self):
        """
        Internal worker thread that processes DB tasks from the queue.
        """
        conn = sqlite3.connect(self.db_path)
        while self.running:
            try:
                task = self.queue.get(timeout=1.0)
                try:
                    task(conn)
                except Exception as e:
                    ls.error(f"Database task failed: {e}")
                finally:
                    self.queue.task_done()
            except queue.Empty:
                continue
        conn.close()

    def close(self):
        self.running = False
        self.worker_thread.join()
