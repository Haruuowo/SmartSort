import os
import hashlib
from difflib import SequenceMatcher

def get_file_hash(filepath: str, chunk_size: int = 8192) -> str:
    """Calculates the SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error hashing {filepath}: {e}")
        return ""

def get_file_size(filepath: str) -> int:
    """Returns the size of the file in bytes."""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return -1

def string_similarity(a: str, b: str) -> float:
    """Returns a similarity ratio between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_duplicate_in_dir(source_filepath: str, target_dir: str, similarity_threshold: float = 0.85):
    """
    Checks if a duplicate or near-duplicate of `source_filepath` exists in `target_dir`.
    Returns a tuple (is_exact_duplicate, duplicate_filepath, reason)
    """
    if not os.path.exists(target_dir):
        return False, None, ""

    source_size = get_file_size(source_filepath)
    source_name = os.path.basename(source_filepath)
    source_hash = None # Lazy evaluate hash

    for item in os.listdir(target_dir):
        target_item_path = os.path.join(target_dir, item)
        if not os.path.isfile(target_item_path):
            continue

        target_size = get_file_size(target_item_path)
        
        # Check 1: Exact size match -> might be exact duplicate
        if source_size == target_size and source_size > 0:
            if source_hash is None:
                source_hash = get_file_hash(source_filepath)
            
            target_hash = get_file_hash(target_item_path)
            
            if source_hash == target_hash and source_hash != "":
                return True, target_item_path, "Exact hash match"

        # Check 2: Near-duplicate by name (if size is somewhat close, e.g., within 10%)
        # This is useful for compressed versions or slight edits, but can be risky if too aggressive.
        # Let's keep it simple: if name is highly similar and size is within 20%
        if target_size > 0 and source_size > 0:
            size_ratio = min(source_size, target_size) / max(source_size, target_size)
            if size_ratio > 0.8:
                sim = string_similarity(source_name, item)
                if sim >= similarity_threshold:
                    return False, target_item_path, f"Near duplicate name (similarity {sim:.2f}) and similar size"
                    
    return False, None, ""
