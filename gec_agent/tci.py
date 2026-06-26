"""
TCI — Temporal Continuity Index layer

Stores a persistent, evolving state across sessions using SQLite.
This is NOT retrieval (RAG). The full state is loaded at session start
and written after every exchange — continuous process, not lookup.
"""

import sqlite3
import json
from datetime import datetime


class TCIStore:
    def __init__(self, agent_id: str, db_path: str = "gec_state.db"):
        self.agent_id = agent_id
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_state (
                    agent_id    TEXT PRIMARY KEY,
                    state_json  TEXT,
                    updated_at  TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_log (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id            TEXT,
                    session_id          TEXT,
                    user_message        TEXT,
                    assistant_response  TEXT,
                    timestamp           TEXT
                )
            """)

    def load(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT state_json FROM agent_state WHERE agent_id = ?",
                (self.agent_id,)
            ).fetchone()
        if row:
            return json.loads(row[0])
        return self._empty_state()

    def save(self, state: dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO agent_state (agent_id, state_json, updated_at)
                   VALUES (?, ?, ?)""",
                (self.agent_id, json.dumps(state, ensure_ascii=False),
                 datetime.now().isoformat())
            )

    def log_exchange(self, session_id: str, user_msg: str, response: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO session_log
                   (agent_id, session_id, user_message, assistant_response, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (self.agent_id, session_id, user_msg, response,
                 datetime.now().isoformat())
            )

    def get_session_count(self) -> int:
        return self.load().get("session_count", 0)

    @staticmethod
    def _empty_state() -> dict:
        return {
            "session_count": 0,
            "created_at": datetime.now().isoformat(),
            "last_updated": None,
            # What the agent currently believes is true / in progress
            "working_hypotheses": [],
            # Things the user has explicitly corrected
            "user_corrections": [],
            # Claims made with stated confidence — for calibration tracking
            "calibration_history": [],
            # Tasks currently in progress across sessions
            "ongoing_tasks": [],
            # User profile built from observation
            "user_profile": {
                "name": None,
                "communication_style": "unknown",
                "expertise_areas": [],
                "preferences": [],
                "known_corrections": []
            },
            # Domain knowledge built during interactions
            "knowledge_built": {},
            # Commitments the agent has made — AVI uses these for consistency
            "consistency_constraints": []
        }
