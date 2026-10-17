import os
import shutil
from datetime import datetime
from typing import Callable, Dict, List, Optional, Set

from .rules import RuleEngine
from .history import log_move, log_moves
from .dedupe import DuplicateIndex

DUPLICATES_DIR = "Duplicates"
FALLBACK_DIR = "Unsorted"
EXIF_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.tif', '.tiff'}

# Files that should never be moved
SKIP_NAMES = {'desktop.ini', 'thumbs.db', '.ds_store', 'icon\r'}
IN_PROGRESS_EXTENSIONS = {'.crdownload', '.part', '.partial', '.download', '.tmp', '.opdownload'}
FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4

_LOG_FLUSH_EVERY = 250


def _read_exif_date(filepath: str) -> Optional[datetime]:
    try:
        from PIL import Image  # imported lazily: Pillow is slow to import
        with Image.open(filepath) as img:
            exif = img.getexif()
            raw = None
            if exif:
                try:
                    raw = exif.get_ifd(0x8769).get(36867)  # DateTimeOriginal
                except Exception:
                    raw = None
                raw = raw or exif.get(36867) or exif.get(306)  # 306 = DateTime
            if raw:
                return datetime.strptime(str(raw).strip()[:19], '%Y:%m:%d %H:%M:%S')
    except Exception:
        pass
    return None


class FileClassifier:
    def __init__(self, target_dir: str, config_path: str):
        self.target_dir = os.path.abspath(target_dir)
        self.rule_engine = RuleEngine(config_path)
        self._uses_exif = self.rule_engine.uses_exif
        self._dupes = DuplicateIndex()
        self._reserved: Set[str] = set()
        self._known_dirs: Set[str] = set()
        self.created_dirs: List[str] = []

    # ── Inspection ───────────────────────────────────────────────────────────

    def _skip_reason(self, filepath: str, st: os.stat_result) -> Optional[str]:
        name = os.path.basename(filepath)
        lower = name.lower()
        if lower in SKIP_NAMES:
            return 'System file'
        if os.path.splitext(lower)[1] in IN_PROGRESS_EXTENSIONS:
            return 'Download still in progress'
        attrs = getattr(st, 'st_file_attributes', 0)
        if attrs & FILE_ATTRIBUTE_SYSTEM:
            return 'System file'
        if attrs & FILE_ATTRIBUTE_HIDDEN or lower.startswith('~$'):
            return 'Hidden or temporary file'
        return None

    def _extract_file_info(self, filepath: str, st: Optional[os.stat_result] = None) -> dict:
        try:
            st = st or os.stat(filepath)
            ctime = datetime.fromtimestamp(min(st.st_ctime, st.st_mtime))
        except (PermissionError, OSError, OverflowError, ValueError):
            ctime = datetime.now()

        info = {
            'name': os.path.basename(filepath).lower(),
            'extension': '',
            'has_exif_date': False,
            'exif_date': None,
            'creation_date': ctime
        }

        _, ext = os.path.splitext(filepath)
        ext = ext.lower()
        if ext:
            info['extension'] = ext
        else:
            # Fallback to content sniffing for extensionless files
            try:
                import filetype
                kind = filetype.guess(filepath)
                if kind is not None:
                    info['extension'] = f".{kind.extension}".lower()
            except Exception:
                pass

        if self._uses_exif and info['extension'] in EXIF_EXTENSIONS:
            dt = _read_exif_date(filepath)
            if dt:
                info['has_exif_date'] = True
                info['exif_date'] = dt

        return info

    def _format_destination(self, template: str, file_info: dict) -> str:
        date_obj = file_info['exif_date'] if file_info['has_exif_date'] else file_info['creation_date']
        dest = template.replace('{year}', date_obj.strftime('%Y'))
        dest = dest.replace('{month}', date_obj.strftime('%m'))
        dest = dest.replace('{day}', date_obj.strftime('%d'))
        return os.path.normpath(os.path.join(self.target_dir, dest))

    def _get_unique_path(self, destination_dir: str, filename: str) -> str:
        """Generates a unique filename if a conflict exists (e.g. file (1).ext)."""
        base, ext = os.path.splitext(filename)
        counter = 1
        new_path = os.path.join(destination_dir, filename)
        while os.path.normcase(new_path) in self._reserved or os.path.exists(new_path):
            new_path = os.path.join(destination_dir, f"{base} ({counter}){ext}")
            counter += 1
        return new_path

    def _ensure_dir(self, directory: str):
        if directory in self._known_dirs:
            return
        missing = []
        probe = directory
        while not os.path.isdir(probe):
            missing.append(probe)
            parent = os.path.dirname(probe)
            if parent == probe:
                break
            probe = parent
        os.makedirs(directory, exist_ok=True)
        self.created_dirs.extend(missing)
        self._known_dirs.add(directory)

    # ── Planning & execution ─────────────────────────────────────────────────

    def plan_file(self, filepath: str) -> Dict:
        """Decides where a file should go without touching the disk."""
        filename = os.path.basename(filepath)
        try:
            st = os.stat(filepath)
        except FileNotFoundError:
            return {'status': 'error', 'file': filename, 'source': filepath, 'reason': 'File not found'}
        except OSError:
            return {'status': 'error', 'file': filename, 'source': filepath, 'reason': 'File is not accessible'}

        skip = self._skip_reason(filepath, st)
        if skip:
            return {'status': 'skipped', 'file': filename, 'source': filepath, 'reason': skip, 'size': st.st_size}

        info = self._extract_file_info(filepath, st)
        rule_name, dest_template = self.rule_engine.evaluate(info)
        if not dest_template:
            rule_name, dest_template = "No matching rule", FALLBACK_DIR

        destination_dir = self._format_destination(dest_template, info)
        status, reason = 'moved', ''

        match = self._dupes.find(filepath, st.st_size, destination_dir)
        if match:
            status = 'duplicate'
            reason = f'Identical to {os.path.basename(match)}'
            destination_dir = os.path.join(self.target_dir, DUPLICATES_DIR)

        target_path = self._get_unique_path(destination_dir, filename)
        self._reserved.add(os.path.normcase(target_path))

        return {
            'status': status,
            'file': filename,
            'source': filepath,
            'rule': rule_name,
            'destination': target_path,
            'folder': os.path.relpath(destination_dir, self.target_dir).replace('\\', '/'),
            'reason': reason,
            'size': st.st_size,
        }

    def _register(self, plan: Dict, readable_path: str):
        if plan['status'] == 'moved':
            self._dupes.add(os.path.dirname(plan['destination']), readable_path,
                            plan.get('size', 0), known_hash_of=plan['source'])

    def _execute(self, plan: Dict):
        target = plan['destination']
        self._ensure_dir(os.path.dirname(target))
        try:
            os.rename(plan['source'], target)  # instant on the same drive, never overwrites
        except OSError:
            if os.path.exists(target):
                raise
            shutil.move(plan['source'], target)

    def process_file(self, filepath: str, dry_run: bool = False) -> Dict:
        """Processes a single file (used by the folder watcher)."""
        plan = self.plan_file(filepath)
        if plan['status'] not in ('moved', 'duplicate'):
            return plan
        if dry_run:
            self._register(plan, filepath)
            return plan
        try:
            self._execute(plan)
            self._register(plan, plan['destination'])
            log_move(filepath, plan['destination'], plan['rule'] if plan['status'] == 'moved' else 'Duplicate detection')
            return plan
        except (PermissionError, OSError) as e:
            return self._error(plan, e)

    @staticmethod
    def _error(plan: Dict, exc: Exception) -> Dict:
        reason = 'File is open in another program' if isinstance(exc, PermissionError) else 'Could not move file'
        return {**plan, 'status': 'error', 'reason': reason, 'destination': None}

    def organize(self, files: List[str], dry_run: bool = False, batch_id: Optional[int] = None,
                 progress: Optional[Callable[[int, int, str], None]] = None,
                 should_cancel: Optional[Callable[[], bool]] = None) -> List[Dict]:
        """Organizes many files, logging moves to history in bulk."""
        self._reserved.clear()
        self._dupes = DuplicateIndex()
        results: List[Dict] = []
        pending_log = []
        total = len(files)

        for i, filepath in enumerate(files, start=1):
            if should_cancel and should_cancel():
                break
            if progress:
                progress(i, total, os.path.basename(filepath))

            plan = self.plan_file(filepath)
            if plan['status'] in ('moved', 'duplicate'):
                if dry_run:
                    self._register(plan, filepath)
                else:
                    try:
                        self._execute(plan)
                        self._register(plan, plan['destination'])
                        rule = plan['rule'] if plan['status'] == 'moved' else 'Duplicate detection'
                        pending_log.append((filepath, plan['destination'], rule))
                    except (PermissionError, OSError) as e:
                        plan = self._error(plan, e)

            results.append(plan)
            if len(pending_log) >= _LOG_FLUSH_EVERY:
                log_moves(batch_id, pending_log)
                pending_log = []

        if pending_log:
            log_moves(batch_id, pending_log)
        return results
