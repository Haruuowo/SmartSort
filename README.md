<div align="center">

# SmartSort

**An intelligent, rule-based file organizer with a terminal-style desktop UI.**

Built with Python · CustomTkinter · SQLite

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Haruuowo/SmartSort)

</div>

---

## What is SmartSort?

SmartSort is a desktop application that organizes your files into categorized folders. It uses content-based detection (not just file extensions), custom YAML rules, EXIF metadata for photos, and built-in deduplication — wrapped in a terminal-style GUI.

> No more manually sorting your Downloads folder. Point SmartSort at a directory, run `sort`, and it handles the rest.

---

## Features

| Feature | Description |
|---|---|
| Desktop GUI | Terminal-style interface — no actual terminal needed |
| Smart Classification | Uses content signatures, not just file extensions |
| EXIF-aware | Sorts photos by date taken (year/month) |
| Deduplication | Detects and skips exact duplicate files |
| Undo System | Every move is logged in SQLite — revert any operation |
| Dry Run Mode | Preview where files would go before committing |
| File Watching | Auto-organize files as they drop into a folder |
| Custom Rules | Define your own sorting rules via YAML config |

---

## Quick Start

### Option 1: Download the Executable
1. Go to [Releases](https://github.com/Haruuowo/SmartSort/releases)
2. Download `SmartSort.exe`
3. Double-click to run — no installation needed

### Option 2: Run from Source
```bash
git clone https://github.com/Haruuowo/SmartSort.git
cd SmartSort
pip install -r requirements.txt
python tui.py
```

---

## Commands

The app uses a terminal-style prompt. Type these commands:

| Command | Description |
|---|---|
| `sort <path>` | Organize files in a directory |
| `dry-run <path>` | Simulate without moving files |
| `sort` / `browse` | Opens a folder picker dialog |
| `ls <path>` | List files in a directory |
| `history` | Show recent move operations |
| `undo` | Undo the last move |
| `undo all` | Undo all recorded moves |
| `clear` | Clear terminal output |
| `pwd` | Print working directory |
| `exit` | Quit |

---

## Custom Rules

Edit `config/rules.yaml` to define sorting rules:

```yaml
rules:
  - name: "Screenshots"
    condition:
      name_contains: ["screenshot", "screen_shot"]
    destination: "Images/Screenshots"

  - name: "Documents"
    condition:
      extensions: [".pdf", ".doc", ".docx", ".txt"]
    destination: "Documents"

  - name: "Photos with EXIF"
    condition:
      extensions: [".jpg", ".jpeg", ".png"]
      has_exif_date: true
    destination: "Photos/{year}/{month}"
```

---

## Project Structure

```
SmartSort/
├── tui.py                  # Desktop GUI (terminal-style)
├── config/
│   └── rules.yaml          # Sorting rules
├── smartsort/
│   ├── classifier.py       # File classification engine
│   ├── cli.py              # CLI interface
│   ├── dedupe.py           # Duplicate detection
│   ├── history.py          # SQLite undo system
│   ├── rules.py            # YAML rule engine
│   └── watcher.py          # Real-time file watcher
├── tests/
│   ├── test_dedupe.py
│   └── test_rules.py
├── dist/
│   └── SmartSort.exe       # Compiled executable
└── requirements.txt
```

---

## Tech Stack

- **Python 3.11** — Core logic
- **CustomTkinter** — Desktop GUI
- **SQLite** — Undo/history database
- **Pillow** — EXIF metadata extraction
- **filetype** — Content-based file detection
- **PyYAML** — Rule configuration
- **PyInstaller** — Executable packaging

---

## Tests

```bash
pytest tests/
```

---

<div align="center">

Made by [Haruuowo](https://github.com/Haruuowo)

</div>
