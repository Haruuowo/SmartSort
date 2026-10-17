"""
Move history / undo system backed by SQLite.

Every "Organize" run is recorded as a *batch* so it can be reverted in one
operation. All writes go through a single shared connection (WAL mode) and are
committed in bulk, which keeps large organize/undo runs fast even on slow disks
or machines with aggressive antivirus scanning.
"""
import json
import os
import shutil
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Callable, Dict, Iterable, List, Optional, Tuple

DB_PATH = os.path.expanduser('~/.smartsort_history.db')

_lock = threading.RLock()
_conn: Optional[sqlite3.Connection] = None
_FLUSH_EVERY = 500


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _get_conn() -> sqlite3.Connection:
    """Returns the shared connection, creating it on first use."""
    global _conn
    with _lock:
        if _conn is None:
            _conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
            try:
                _conn.execute('PRAGMA journal_mode=WAL')
                _conn.execute('PRAGMA synchronous=NORMAL')
            except sqlite3.DatabaseError:
                pass
        return _conn


def _columns(conn, table: str) -> set:
    return {row[1] for row in conn.execute(f'PRAGMA table_info({table})')}


def init_db():
    """Initializes the database schema and migrates older history files."""
    with _lock:
        conn = _get_conn()
        with conn:
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
            conn.execute('''
                CREATE TABLE IF NOT EXISTS batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_dir TEXT,
                    created_at TEXT,
                    created_dirs TEXT DEFAULT '[]'
                )
            ''')
            if 'batch_id' not in _columns(conn, 'moves'):
                conn.execute('ALTER TABLE moves ADD COLUMN batch_id INTEGER')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_moves_batch ON moves(batch_id, undone)')
        _migrate_legacy_rows(conn)


def _migrate_legacy_rows(conn):
    """Groups pre-batch history rows into sessions so they can still be undone."""
    rows = conn.execute(
        'SELECT id, original_path, timestamp FROM moves WHERE batch_id IS NULL ORDER BY id'
    ).fetchall()
    if not rows:
        return

    groups: List[List[int]] = []
    meta: List[Tuple[str, str]] = []
    last_dir, last_ts = None, None
    for move_id, original, ts in rows:
        folder = os.path.dirname(original or '')
        try:
            ts_dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
        except (TypeError, ValueError):
            ts_dt = None
        new_group = (
            not groups or folder != last_dir or ts_dt is None or last_ts is None
            or abs((ts_dt - last_ts).total_seconds()) > 120
        )
        if new_group:
            groups.append([])
            created = ts_dt.replace(tzinfo=timezone.utc).isoformat() if ts_dt else _now_iso()
            meta.append((folder, created))
        groups[-1].append(move_id)
        last_dir, last_ts = folder, ts_dt

    with conn:
        for ids, (folder, created) in zip(groups, meta):
            cur = conn.execute(
                'INSERT INTO batches (target_dir, created_at, created_dirs) VALUES (?, ?, ?)',
                (folder, created, '[]'),
            )
            conn.executemany('UPDATE moves SET batch_id = ? WHERE id = ?',
                             [(cur.lastrowid, i) for i in ids])


# ── Writing ──────────────────────────────────────────────────────────────────

def create_batch(target_dir: str) -> int:
    with _lock:
        conn = _get_conn()
        with conn:
            cur = conn.execute(
                'INSERT INTO batches (target_dir, created_at, created_dirs) VALUES (?, ?, ?)',
                (os.path.abspath(target_dir), _now_iso(), '[]'),
            )
            return cur.lastrowid


def log_moves(batch_id: Optional[int], entries: Iterable[Tuple[str, str, str]]):
    """Bulk-inserts (original_path, destination_path, rule_name) rows in one transaction."""
    rows = [(str(src), str(dst), rule, batch_id) for src, dst, rule in entries]
    if not rows:
        return
    with _lock:
        conn = _get_conn()
        with conn:
            conn.executemany(
                'INSERT INTO moves (original_path, destination_path, rule_name, batch_id) VALUES (?, ?, ?, ?)',
                rows,
            )


def log_move(original_path: str, destination_path: str, rule_name: str = "Unknown",
             batch_id: Optional[int] = None):
    """Logs a single file move (used by the folder watcher)."""
    if batch_id is None:
        batch_id = create_batch(os.path.dirname(str(original_path)))
    log_moves(batch_id, [(original_path, destination_path, rule_name)])


def finalize_batch(batch_id: int, created_dirs: Optional[List[str]] = None):
    """Stores folders created during the batch; removes the batch if nothing moved."""
    with _lock:
        conn = _get_conn()
        with conn:
            count = conn.execute('SELECT COUNT(*) FROM moves WHERE batch_id = ?', (batch_id,)).fetchone()[0]
            if count == 0:
                conn.execute('DELETE FROM batches WHERE id = ?', (batch_id,))
            else:
                conn.execute('UPDATE batches SET created_dirs = ? WHERE id = ?',
                             (json.dumps(created_dirs or []), batch_id))


# ── Reading ──────────────────────────────────────────────────────────────────

def list_batches(limit: int = 50) -> List[Dict]:
    with _lock:
        rows = _get_conn().execute('''
            SELECT b.id, b.target_dir, b.created_at,
                   COUNT(m.id) AS total,
                   COALESCE(SUM(CASE WHEN m.undone = 0 THEN 1 ELSE 0 END), 0) AS remaining
            FROM batches b
            LEFT JOIN moves m ON m.batch_id = b.id
            GROUP BY b.id
            HAVING total > 0
            ORDER BY b.id DESC
            LIMIT ?
        ''', (int(limit),)).fetchall()
    return [
        {'id': r[0], 'target_dir': r[1] or '', 'created_at': r[2], 'total': r[3], 'remaining': r[4]}
        for r in rows
    ]


def get_batch_moves(batch_id: int, limit: int = 5000) -> List[Dict]:
    with _lock:
        rows = _get_conn().execute('''
            SELECT id, original_path, destination_path, rule_name, undone
            FROM moves WHERE batch_id = ? ORDER BY id LIMIT ?
        ''', (int(batch_id), int(limit))).fetchall()
    return [
        {'id': r[0], 'src': r[1], 'dest': r[2], 'rule': r[3] or '', 'undone': bool(r[4])}
        for r in rows
    ]


def get_history(limit=None):
    """Legacy helper: recent moves that haven't been undone (newest first)."""
    query = '''
        SELECT id, original_path, destination_path, rule_name, timestamp
        FROM moves WHERE undone = 0 ORDER BY id DESC
    '''
    params: tuple = ()
    if limit:
        query += ' LIMIT ?'
        params = (int(limit),)
    with _lock:
        return _get_conn().execute(query, params).fetchall()


def latest_undoable_batch() -> Optional[int]:
    with _lock:
        row = _get_conn().execute('''
            SELECT batch_id FROM moves WHERE undone = 0 AND batch_id IS NOT NULL
            ORDER BY id DESC LIMIT 1
        ''').fetchone()
    return row[0] if row else None


# ── Undo ─────────────────────────────────────────────────────────────────────

def _mark_undone(ids: List[int]):
    if not ids:
        return
    with _lock:
        conn = _get_conn()
        with conn:
            conn.executemany('UPDATE moves SET undone = 1 WHERE id = ?', [(i,) for i in ids])


def mark_undone(move_id: int):
    _mark_undone([move_id])


def _unique_path(path: str) -> str:
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    counter = 1
    while True:
        candidate = f"{base} (restored{'' if counter == 1 else ' ' + str(counter)}){ext}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def _move(src: str, dst: str):
    try:
        os.rename(src, dst)  # instant on the same volume, never overwrites on Windows
    except OSError:
        if os.path.exists(dst):
            raise
        shutil.move(src, dst)


def undo_move(move_record) -> bool:
    """Legacy helper: undo a single move record (id, original, destination, ...)."""
    move_id, original_path, destination_path = move_record[0], move_record[1], move_record[2]
    if not os.path.exists(destination_path):
        return False
    try:
        os.makedirs(os.path.dirname(original_path), exist_ok=True)
        _move(destination_path, _unique_path(original_path))
        mark_undone(move_id)
        return True
    except Exception as e:
        print(f"Error undoing move for {destination_path}: {e}")
        return False


def _prune_created_dirs(created_dirs: List[str]) -> int:
    """Removes folders the batch created, deepest first, only if they are empty."""
    removed = 0
    for d in sorted(set(created_dirs), key=lambda p: p.count(os.sep), reverse=True):
        try:
            if os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
                removed += 1
        except OSError:
            continue
    return removed


def undo_batch(batch_id: Optional[int] = None,
               progress: Optional[Callable[[int, int, str], None]] = None) -> Dict:
    """
    Reverts every remaining move in a batch (the latest one if batch_id is None).
    Files are restored newest-first; if the original location is now occupied the
    file is restored next to it with a "(restored)" suffix instead of overwriting.
    """
    if batch_id is None:
        batch_id = latest_undoable_batch()
    result = {'batch_id': batch_id, 'restored': 0, 'renamed': 0, 'missing': 0,
              'failed': 0, 'errors': [], 'folders_removed': 0, 'total': 0}
    if batch_id is None:
        return result

    with _lock:
        conn = _get_conn()
        rows = conn.execute('''
            SELECT id, original_path, destination_path FROM moves
            WHERE batch_id = ? AND undone = 0 ORDER BY id DESC
        ''', (batch_id,)).fetchall()
        meta = conn.execute('SELECT created_dirs FROM batches WHERE id = ?', (batch_id,)).fetchone()

    total = len(rows)
    result['total'] = total
    pending: List[int] = []
    known_dirs = set()

    for i, (move_id, original, destination) in enumerate(rows, start=1):
        name = os.path.basename(original)
        if progress:
            progress(i, total, name)
        if not os.path.exists(destination):
            result['missing'] += 1
            pending.append(move_id)  # can never be restored; don't keep it pending forever
        else:
            target = original
            if os.path.exists(target):
                target = _unique_path(original)
                result['renamed'] += 1
            try:
                parent = os.path.dirname(target)
                if parent not in known_dirs:
                    os.makedirs(parent, exist_ok=True)
                    known_dirs.add(parent)
                _move(destination, target)
                result['restored'] += 1
                pending.append(move_id)
            except Exception as e:
                result['failed'] += 1
                if len(result['errors']) < 50:
                    result['errors'].append({'file': name, 'reason': str(e)})
        if len(pending) >= _FLUSH_EVERY:
            _mark_undone(pending)
            pending = []

    _mark_undone(pending)

    try:
        created_dirs = json.loads(meta[0]) if meta and meta[0] else []
    except (TypeError, ValueError):
        created_dirs = []
    result['folders_removed'] = _prune_created_dirs(created_dirs)
    return result


# Initialize the DB when the module loads
try:
    init_db()
except sqlite3.Error as _e:  # never crash the app because history is unavailable
    print(f"SmartSort history unavailable: {_e}")
