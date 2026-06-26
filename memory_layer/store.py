# store.py
# Saves exchanges + their embeddings to SQLite.
# Retrieves the top-N most semantically similar past exchanges.

import sqlite3
import numpy as np
import json
from typing import List, Tuple
from parser import Exchange


DB_FILE = "memory.db"


def init_db(db_path: str = DB_FILE):
    """Create the database and table if they don't exist."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exchanges (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            role        TEXT NOT NULL,
            text        TEXT NOT NULL,
            timestamp   REAL,
            source      TEXT,
            conv_id     TEXT,
            embedding   BLOB NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_exchange(exchange: Exchange, embedding: np.ndarray, db_path: str = DB_FILE):
    """Save a single exchange with its embedding."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO exchanges (role, text, timestamp, source, conv_id, embedding) VALUES (?,?,?,?,?,?)",
        (
            exchange.role,
            exchange.text,
            exchange.timestamp,
            exchange.source,
            exchange.conversation_id,
            embedding.astype(np.float32).tobytes()
        )
    )
    conn.commit()
    conn.close()


def save_batch(exchanges: List[Exchange], embeddings: np.ndarray, db_path: str = DB_FILE):
    """Save many exchanges at once — much faster than one by one."""
    conn = sqlite3.connect(db_path)
    rows = [
        (e.role, e.text, e.timestamp, e.source, e.conversation_id,
         emb.astype(np.float32).tobytes())
        for e, emb in zip(exchanges, embeddings)
    ]
    conn.executemany(
        "INSERT INTO exchanges (role, text, timestamp, source, conv_id, embedding) VALUES (?,?,?,?,?,?)",
        rows
    )
    conn.commit()
    conn.close()
    return len(rows)


def retrieve_top(query_embedding: np.ndarray, top_n: int = 5, db_path: str = DB_FILE) -> List[Tuple[float, Exchange]]:
    """
    Find the top-N most relevant past exchanges.
    Returns list of (similarity_score, Exchange) tuples, sorted best-first.
    """
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT role, text, timestamp, source, conv_id, embedding FROM exchanges"
    ).fetchall()
    conn.close()

    if not rows:
        return []

    results = []
    for role, text, ts, source, conv_id, emb_bytes in rows:
        stored_vec = np.frombuffer(emb_bytes, dtype=np.float32)
        score = float(np.dot(query_embedding, stored_vec))
        results.append((score, Exchange(role, text, ts, source, conv_id)))

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_n]


def count(db_path: str = DB_FILE) -> int:
    """Total number of stored exchanges."""
    conn = sqlite3.connect(db_path)
    n = conn.execute("SELECT COUNT(*) FROM exchanges").fetchone()[0]
    conn.close()
    return n
