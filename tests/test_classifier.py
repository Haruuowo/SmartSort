import os
import tempfile
import yaml
import pytest
from unittest.mock import patch
from smartsort.classifier import FileClassifier
import smartsort.history as history

@pytest.fixture
def sample_config(tmp_path):
    rules_data = {
        'rules': [
            {
                'name': 'Documents',
                'condition': {'extensions': ['.pdf', '.txt']},
                'destination': 'Docs'
            },
            {
                'name': 'Images',
                'condition': {'extensions': ['.jpg', '.png']},
                'destination': 'Pics'
            }
        ]
    }
    cfg_file = tmp_path / "rules.yaml"
    cfg_file.write_text(yaml.dump(rules_data))
    return str(cfg_file)

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_history.db"
    with patch.object(history, 'DB_PATH', str(db_file)), \
         patch.object(history, '_conn', None):
        history.init_db()
        yield db_file

def test_classifier_organize_and_dry_run(sample_config, temp_db, tmp_path):
    target = tmp_path / "workspace"
    target.mkdir()
    
    f1 = target / "notes.txt"
    f1.write_text("my notes")
    f2 = target / "photo.jpg"
    f2.write_text("photo data")
    
    classifier = FileClassifier(str(target), sample_config)
    
    # Dry run preview
    plans = classifier.organize([str(f1), str(f2)], dry_run=True)
    assert len(plans) == 2
    assert plans[0]['status'] == 'moved'
    assert plans[0]['folder'] == 'Docs'
    assert f1.exists() # not moved in dry run
    assert f2.exists()
    
    # Real run
    batch_id = history.create_batch(str(target))
    results = classifier.organize([str(f1), str(f2)], dry_run=False, batch_id=batch_id)
    history.finalize_batch(batch_id, classifier.created_dirs)
    
    assert not f1.exists()
    assert not f2.exists()
    assert (target / "Docs" / "notes.txt").exists()
    assert (target / "Pics" / "photo.jpg").exists()
    
    # Undo the batch
    undo_res = history.undo_batch(batch_id)
    assert undo_res['restored'] == 2
    assert f1.exists()
    assert f2.exists()
    assert not (target / "Docs").exists() # empty created dir pruned
    assert not (target / "Pics").exists()

def test_classifier_duplicate_detection(sample_config, temp_db, tmp_path):
    target = tmp_path / "workspace"
    target.mkdir()
    
    docs_dir = target / "Docs"
    docs_dir.mkdir()
    existing = docs_dir / "existing.txt"
    existing.write_text("duplicate text content")
    
    incoming = target / "incoming.txt"
    incoming.write_text("duplicate text content")
    
    classifier = FileClassifier(str(target), sample_config)
    batch_id = history.create_batch(str(target))
    res = classifier.organize([str(incoming)], dry_run=False, batch_id=batch_id)
    history.finalize_batch(batch_id, classifier.created_dirs)
    
    assert res[0]['status'] == 'duplicate'
    assert (target / "Duplicates" / "incoming.txt").exists()
