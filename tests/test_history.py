import os
import tempfile
import sqlite3
import pytest
from unittest.mock import patch
import smartsort.history as history

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_history.db"
    with patch.object(history, 'DB_PATH', str(db_file)), \
         patch.object(history, '_conn', None):
        history.init_db()
        yield db_file

def test_batch_creation_and_logging(temp_db, tmp_path):
    target = tmp_path / "target_folder"
    target.mkdir()
    
    batch_id = history.create_batch(str(target))
    assert batch_id > 0
    
    f1_src = str(target / "doc1.pdf")
    f1_dst = str(target / "Documents" / "doc1.pdf")
    f2_src = str(target / "doc2.pdf")
    f2_dst = str(target / "Documents" / "doc2.pdf")
    
    history.log_moves(batch_id, [
        (f1_src, f1_dst, "Documents"),
        (f2_src, f2_dst, "Documents")
    ])
    history.finalize_batch(batch_id, [str(target / "Documents")])
    
    batches = history.list_batches()
    assert len(batches) == 1
    assert batches[0]['id'] == batch_id
    assert batches[0]['total'] == 2
    assert batches[0]['remaining'] == 2
    
    moves = history.get_batch_moves(batch_id)
    assert len(moves) == 2
    assert moves[0]['src'] == f1_src
    assert moves[0]['dest'] == f1_dst
    assert moves[0]['undone'] is False

def test_undo_batch(temp_db, tmp_path):
    folder = tmp_path / "downloads"
    folder.mkdir()
    
    sub = folder / "Documents"
    sub.mkdir()
    
    # Original files moved to sub
    orig_file = folder / "my_doc.pdf"
    moved_file = sub / "my_doc.pdf"
    moved_file.write_text("dummy content")
    
    batch_id = history.create_batch(str(folder))
    history.log_moves(batch_id, [(str(orig_file), str(moved_file), "Documents")])
    history.finalize_batch(batch_id, [str(sub)])
    
    assert moved_file.exists()
    assert not orig_file.exists()
    
    # Run undo
    res = history.undo_batch(batch_id)
    assert res['restored'] == 1
    assert res['failed'] == 0
    assert orig_file.exists()
    assert not moved_file.exists()
    assert not sub.exists() # Should prune empty created folder

def test_undo_batch_conflict_avoids_overwrite(temp_db, tmp_path):
    folder = tmp_path / "downloads"
    folder.mkdir()
    sub = folder / "Documents"
    sub.mkdir()
    
    orig_file = folder / "test.txt"
    moved_file = sub / "test.txt"
    moved_file.write_text("moved content")
    
    batch_id = history.create_batch(str(folder))
    history.log_moves(batch_id, [(str(orig_file), str(moved_file), "Documents")])
    history.finalize_batch(batch_id, [str(sub)])
    
    # A new file with the original name is placed before undo
    orig_file.write_text("new content")
    
    res = history.undo_batch(batch_id)
    assert res['restored'] == 1
    assert res['renamed'] == 1
    
    # Verify original file untouched
    assert orig_file.read_text() == "new content"
    
    # Restored file exists with unique name
    restored = folder / "test (restored).txt"
    assert restored.exists()
    assert restored.read_text() == "moved content"
