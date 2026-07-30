import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.expanduser('~/.smartsort_history.db')

def _get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initializes the SQLite database for tracking file movements."""
    with _get_conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_path TEXT NOT NULL,
                destination_path TEXT NOT NULL,
                rule_name TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                undone BOOLEAN DEFAULT 0
            )
        ''')

def log_move(original_path: str, destination_path: str, rule_name: str = "Unknown"):
    """Logs a file move operation."""
    with _get_conn() as conn:
        conn.execute('''
            INSERT INTO moves (original_path, destination_path, rule_name)
            VALUES (?, ?, ?)
        ''', (str(original_path), str(destination_path), rule_name))

def get_history(limit=None):
    """Retrieves the history of moves that haven't been undone yet."""
    with _get_conn() as conn:
        query = '''
            SELECT id, original_path, destination_path, rule_name, timestamp
            FROM moves
            WHERE undone = 0
            ORDER BY timestamp DESC
        '''
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = conn.execute(query)
        return cursor.fetchall()

def mark_undone(move_id: int):
    """Marks a specific move as undone in the database."""
    with _get_conn() as conn:
        conn.execute('UPDATE moves SET undone = 1 WHERE id = ?', (move_id,))

def undo_move(move_record) -> bool:
    """
    Attempts to undo a specific move.
    Returns True if successful, False otherwise.
    """
    move_id, original_path, destination_path, _, _ = move_record
    
    if os.path.exists(destination_path):
        try:
            # Ensure the original directory exists
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            shutil.move(destination_path, original_path)
            mark_undone(move_id)
            return True
        except Exception as e:
            print(f"Error undoing move for {destination_path}: {e}")
            return False
    else:
        print(f"Cannot undo: File not found at {destination_path}")
        return False

# Initialize the DB when the module loads
init_db()
