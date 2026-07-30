import os
from collections import defaultdict
from typing import Dict, List

from .classifier import FileClassifier

def analyze_directory(target_dir: str, config_path: str) -> Dict:
    """
    Analyzes target_dir in WizTree style:
    - Breakdown by category (file count, total bytes, % of total size, visual bar)
    - Top 10 largest files
    """
    summary = {
        'total_files': 0,
        'total_size': 0,
        'categories': defaultdict(lambda: {'count': 0, 'size': 0}),
        'extensions': defaultdict(lambda: {'count': 0, 'size': 0}),
        'top_files': []
    }

    if not os.path.exists(target_dir):
        return summary

    classifier = FileClassifier(target_dir, config_path)
    all_files_info = []

    try:
        filenames = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
    except Exception:
        return summary

    for filename in filenames:
        filepath = os.path.join(target_dir, filename)
        try:
            size = os.path.getsize(filepath)
        except OSError:
            size = 0

        summary['total_files'] += 1
        summary['total_size'] += size

        info = classifier._extract_file_info(filepath)
        rule_name, dest_template = classifier.rule_engine.evaluate(info)
        category = dest_template.split('/')[0] if dest_template else "Unsorted"
        ext = info.get('extension', 'no-ext') or 'no-ext'

        summary['categories'][category]['count'] += 1
        summary['categories'][category]['size'] += size

        summary['extensions'][ext]['count'] += 1
        summary['extensions'][ext]['size'] += size

        all_files_info.append({
            'name': filename,
            'size': size,
            'category': category,
            'ext': ext
        })

    # Sort largest files
    all_files_info.sort(key=lambda x: x['size'], reverse=True)
    summary['top_files'] = all_files_info[:10]

    return summary

def format_size(b: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"

def generate_bar(pct: float, width: int = 12) -> str:
    """Generates ASCII visual bar e.g. [████████░░]"""
    filled = int(round(width * (pct / 100.0)))
    filled = min(max(filled, 0), width)
    return "█" * filled + "░" * (width - filled)
