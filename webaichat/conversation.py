import sqlite3
import os
import json
from typing import List, Optional, Dict
from datetime import datetime

from .utils import DB_PATH, logger


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_query TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            source_chunks TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized")


def create_session(session_id: str) -> str:
    conn = _get_connection()
    conn.execute(
        "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, "system", "Conversation started"),
    )
    conn.commit()
    conn.close()
    return session_id


def add_message(session_id: str, role: str, content: str):
    conn = _get_connection()
    last_msg = conn.execute(
        "SELECT id, content FROM conversations WHERE session_id = ? AND role = ? ORDER BY id DESC LIMIT 1",
        (session_id, role),
    ).fetchone()
    if last_msg and last_msg[0] is not None and last_msg[1] == content:
        conn.close()
        return
    conn.execute(
        "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content),
    )
    conn.commit()
    conn.close()


def get_messages(session_id: str, limit: int = 50) -> List[dict]:
    conn = _get_connection()
    rows = conn.execute(
        "SELECT role, content, timestamp FROM conversations WHERE session_id = ? AND role != 'system' ORDER BY id ASC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]} for r in rows]


def log_query(session_id: str, user_query: str, response: str, source_chunks: str):
    conn = _get_connection()
    conn.execute(
        "INSERT INTO logs (session_id, user_query, assistant_response, source_chunks) VALUES (?, ?, ?, ?)",
        (session_id, user_query, response, source_chunks),
    )
    conn.commit()
    conn.close()


def get_all_conversations(limit: int = 100) -> List[dict]:
    conn = _get_connection()
    rows = conn.execute(
        """
        SELECT session_id, MAX(id) as max_id
        FROM logs
        GROUP BY session_id
        ORDER BY max_id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    
    result = []
    for r in rows:
        session_id = r["session_id"]
        
        user_query = ""
        user_rows = conn.execute(
            "SELECT content FROM conversations WHERE session_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1",
            (session_id,),
        ).fetchall()
        if user_rows:
            user_query = user_rows[0]["content"]
        
        bot_response = ""
        bot_rows = conn.execute(
            "SELECT content FROM conversations WHERE session_id = ? AND role = 'assistant' ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchall()
        if bot_rows:
            bot_response = bot_rows[0]["content"]
        
        timestamp = ""
        ts_rows = conn.execute(
            "SELECT timestamp FROM logs WHERE session_id = ? ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchall()
        if ts_rows:
            timestamp = ts_rows[0]["timestamp"]
        
        result.append({
            "session_id": session_id,
            "user_query": user_query,
            "bot_response": bot_response,
            "timestamp": timestamp,
        })
    
    conn.close()
    return result


def get_conversation_by_id(session_id: str) -> dict:
    conn = _get_connection()
    
    user_query = ""
    user_rows = conn.execute(
        "SELECT content FROM conversations WHERE session_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1",
        (session_id,),
    ).fetchall()
    if user_rows:
        user_query = user_rows[0]["content"]
    
    bot_response = ""
    bot_rows = conn.execute(
        "SELECT content FROM conversations WHERE session_id = ? AND role = 'assistant' ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchall()
    if bot_rows:
        bot_response = bot_rows[0]["content"]
    
    msgs = get_messages(session_id)
    
    conn.close()
    
    return {
        "session_id": session_id,
        "user_query": user_query,
        "bot_response": bot_response,
        "messages": msgs,
    }


def search_conversations(query: str, limit: int = 50) -> List[dict]:
    conn = _get_connection()
    rows = conn.execute(
        "SELECT DISTINCT session_id, timestamp FROM logs WHERE user_query LIKE ? OR assistant_response LIKE ? ORDER BY id DESC LIMIT ?",
        (f"%{query}%", f"%{query}%", limit),
    ).fetchall()
    
    result = []
    for r in rows:
        session_id = r["session_id"]
        user_query = ""
        user_rows = conn.execute(
            "SELECT content FROM conversations WHERE session_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1",
            (session_id,),
        ).fetchall()
        if user_rows:
            user_query = user_rows[0]["content"]
        
        bot_response = ""
        bot_rows = conn.execute(
            "SELECT content FROM conversations WHERE session_id = ? AND role = 'assistant' ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchall()
        if bot_rows:
            bot_response = bot_rows[0]["content"]
        
        result.append({
            "session_id": session_id,
            "user_query": user_query,
            "bot_response": bot_response,
            "timestamp": r["timestamp"],
        })
    
    conn.close()
    return result


def delete_conversation(session_id: str):
    conn = _get_connection()
    conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM logs WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    logger.info(f"Deleted conversation for session {session_id}")


def export_conversations(format: str = "json") -> str:
    conn = _get_connection()
    rows = conn.execute(
        "SELECT session_id, user_query, assistant_response, source_chunks, timestamp FROM logs ORDER BY id"
    ).fetchall()
    conn.close()
    data = [
        {
            "session_id": r["session_id"],
            "user_query": r["user_query"],
            "assistant_response": r["assistant_response"],
            "source_chunks": json.loads(r["source_chunks"]) if r["source_chunks"] else [],
            "timestamp": r["timestamp"],
        }
        for r in rows
    ]
    if format == "csv":
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["session_id", "user_query", "assistant_response", "timestamp"])
        writer.writeheader()
        for row in data:
            writer.writerow({
                "session_id": row["session_id"],
                "user_query": row["user_query"],
                "assistant_response": row["assistant_response"],
                "timestamp": row["timestamp"],
            })
        return output.getvalue()
    return json.dumps(data, indent=2)


def get_stats() -> dict:
    conn = _get_connection()
    total_convs = conn.execute("SELECT COUNT(DISTINCT session_id) FROM conversations").fetchone()[0]
    total_logs = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    conn.close()
    return {"total_conversations": total_convs, "total_queries": total_logs}
