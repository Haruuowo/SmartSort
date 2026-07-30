# SmartSort

SmartSort is a rule-based Python file and folder organizer CLI tool. It intelligently organizes files based on their type, EXIF metadata, name patterns, and avoids duplicates. It features a robust undo system and a dry-run mode for safety.

## Features
- **File Watching**: Automatically organize files as they drop into a folder.
- **Rule-based Sorting**: Uses content signatures (not just extensions) and custom user-defined YAML rules.
- **Deduplication**: Hashes files to avoid moving exact duplicates and can catch similar filenames.
- **Undo System**: Every move is logged in a local SQLite database, allowing you to instantly revert any file sort operation.
- **Dry-run Mode**: Preview where files *would* go before committing to the sort.

## Setup
1. Ensure Python 3.9+ is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Edit the rules in `config/rules.yaml`.

## Usage
Run the CLI using:
```bash
python -m smartsort --help
```

### Commands

**Sort a folder immediately:**
```bash
python -m smartsort sort "C:\Path\To\Folder"
```

**Watch a folder in real-time:**
```bash
python -m smartsort watch "C:\Path\To\Folder"
```

**Preview a sort without moving files:**
```bash
python -m smartsort dry-run "C:\Path\To\Folder"
```

**Undo the last operation(s):**
```bash
python -m smartsort undo --limit 5
# Or undo everything:
python -m smartsort undo --all
```

**View active rules:**
```bash
python -m smartsort rules
```

## Running Tests
Run the test suite using pytest:
```bash
pytest tests/
```
