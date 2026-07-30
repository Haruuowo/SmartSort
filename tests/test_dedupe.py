import pytest
import os
import tempfile
from smartsort.dedupe import string_similarity, find_duplicate_in_dir, get_file_hash

def test_string_similarity():
    assert string_similarity("hello", "hello") == 1.0
    assert string_similarity("hello", "world") < 0.5
    assert string_similarity("Receipt_2023.pdf", "receipt_2023_copy.pdf") > 0.7

def test_find_duplicate(tmp_path):
    source_file = tmp_path / "source.txt"
    source_file.write_text("Hello World!")
    
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    # Not duplicate
    is_dup, _, _ = find_duplicate_in_dir(str(source_file), str(target_dir))
    assert not is_dup
    
    # Exact duplicate
    exact_dup = target_dir / "target.txt"
    exact_dup.write_text("Hello World!")
    
    is_dup, dup_path, reason = find_duplicate_in_dir(str(source_file), str(target_dir))
    assert is_dup
    assert dup_path == str(exact_dup)
    assert "hash match" in reason
    
    # Near duplicate (different content but similar name and size)
    # This requires more complex mocking, but we test the exact duplicate above.
