import os
import shutil
import filetype
from PIL import Image, ExifTags
from datetime import datetime
from typing import Tuple, Dict

from .rules import RuleEngine
from .history import log_move
from .dedupe import find_duplicate_in_dir

class FileClassifier:
    def __init__(self, target_dir: str, config_path: str):
        self.target_dir = os.path.abspath(target_dir)
        self.rule_engine = RuleEngine(config_path)

    def _extract_file_info(self, filepath: str) -> dict:
        info = {
            'name': os.path.basename(filepath).lower(),
            'extension': '',
            'has_exif_date': False,
            'exif_date': None,
            'creation_date': datetime.fromtimestamp(os.path.getctime(filepath))
        }

        # Primary extension from filename
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()

        if ext:
            info['extension'] = ext
        else:
            # Fallback to content sniffing for extensionless files
            try:
                kind = filetype.guess(filepath)
                if kind is not None:
                    info['extension'] = f".{kind.extension}".lower()
            except Exception:
                pass

        # EXIF extraction for images
        if info['extension'] in ['.jpg', '.jpeg', '.png', '.webp']:
            try:
                with Image.open(filepath) as img:
                    exif_data = img._getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag = ExifTags.TAGS.get(tag_id, tag_id)
                            if tag == 'DateTimeOriginal':
                                try:
                                    dt = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                                    info['has_exif_date'] = True
                                    info['exif_date'] = dt
                                except ValueError:
                                    pass
                                break
            except Exception:
                pass # Not an image or no EXIF

        return info

    def _format_destination(self, template: str, file_info: dict) -> str:
        date_obj = file_info['exif_date'] if file_info['has_exif_date'] else file_info['creation_date']
        
        # Format the template
        dest = template.replace('{year}', date_obj.strftime('%Y'))
        dest = dest.replace('{month}', date_obj.strftime('%m'))
        dest = dest.replace('{day}', date_obj.strftime('%d'))
        
        return os.path.join(self.target_dir, dest)

    def _get_unique_path(self, destination_dir: str, filename: str) -> str:
        """Generates a unique filename if conflict exists (e.g., file (1).ext)"""
        base, ext = os.path.splitext(filename)
        counter = 1
        new_path = os.path.join(destination_dir, filename)
        while os.path.exists(new_path):
            new_path = os.path.join(destination_dir, f"{base} ({counter}){ext}")
            counter += 1
        return new_path

    def process_file(self, filepath: str, dry_run: bool = False) -> Dict:
        """
        Processes a single file. Returns a summary dictionary.
        """
        if not os.path.exists(filepath):
            return {'status': 'error', 'reason': 'File not found'}

        info = self._extract_file_info(filepath)
        rule_name, dest_template = self.rule_engine.evaluate(info)

        if not dest_template:
            # Fallback for files that don't match rules
            rule_name = "Default fallback"
            dest_template = "Unsorted"

        destination_dir = self._format_destination(dest_template, info)
        
        # Check duplicates
        is_exact, dup_path, reason = find_duplicate_in_dir(filepath, destination_dir)
        
        if is_exact:
            filename = os.path.basename(filepath)
            dup_dir = os.path.join(self.target_dir, "Duplicates")
            target_path = self._get_unique_path(dup_dir, filename)
            
            if not dry_run:
                os.makedirs(dup_dir, exist_ok=True)
                shutil.move(filepath, target_path)
                log_move(filepath, target_path, "Duplicate detection")

            return {
                'status': 'duplicate',
                'file': filename,
                'rule': rule_name,
                'destination': target_path,
                'reason': f'Exact match of {os.path.basename(dup_path or "")} -> moved to Duplicates'
            }
            
        filename = os.path.basename(filepath)
        target_path = self._get_unique_path(destination_dir, filename)

        if not dry_run:
            os.makedirs(destination_dir, exist_ok=True)
            shutil.move(filepath, target_path)
            log_move(filepath, target_path, rule_name)

        return {
            'status': 'moved',
            'file': filename,
            'rule': rule_name,
            'destination': target_path
        }
