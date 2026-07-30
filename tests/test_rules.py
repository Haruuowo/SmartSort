import pytest
import os
import tempfile
import yaml
from smartsort.rules import RuleEngine

@pytest.fixture
def dummy_rules_file():
    rules_data = {
        'rules': [
            {
                'name': 'Receipts',
                'condition': {'name_contains': ['receipt', 'invoice']},
                'destination': 'Finance/Receipts'
            },
            {
                'name': 'Photos',
                'condition': {'extensions': ['.jpg', '.png'], 'has_exif_date': True},
                'destination': 'Photos/{year}'
            }
        ]
    }
    fd, path = tempfile.mkstemp(suffix='.yaml')
    with os.fdopen(fd, 'w') as f:
        yaml.dump(rules_data, f)
    yield path
    os.remove(path)

def test_rule_engine_receipt(dummy_rules_file):
    engine = RuleEngine(dummy_rules_file)
    file_info = {'name': 'my_receipt_2023.pdf', 'extension': '.pdf', 'has_exif_date': False}
    
    rule_name, dest = engine.evaluate(file_info)
    assert rule_name == 'Receipts'
    assert dest == 'Finance/Receipts'

def test_rule_engine_photo(dummy_rules_file):
    engine = RuleEngine(dummy_rules_file)
    file_info = {'name': 'vacation.jpg', 'extension': '.jpg', 'has_exif_date': True}
    
    rule_name, dest = engine.evaluate(file_info)
    assert rule_name == 'Photos'
    assert dest == 'Photos/{year}'

def test_rule_engine_nomatch(dummy_rules_file):
    engine = RuleEngine(dummy_rules_file)
    file_info = {'name': 'random_file.txt', 'extension': '.txt', 'has_exif_date': False}
    
    rule_name, dest = engine.evaluate(file_info)
    assert rule_name is None
    assert dest is None
