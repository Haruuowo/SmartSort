<div align="center">

# ⚡ SmartSort

**An intelligent, rule-based file organizer with a sleek desktop GUI.**

Built with Python · CustomTkinter · SQLite

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Haruuowo/SmartSort)

</div>

---

## 🎯 What is SmartSort?

SmartSort is a **desktop application** that intelligently organizes your messy files into categorized folders. It uses content-based detection (not just file extensions), custom YAML rules, EXIF metadata for photos, and built-in deduplication — all wrapped in a modern dark-themed GUI.

> **No more manually sorting your Downloads folder.** Just point SmartSort at a directory, hit Organize, and watch the magic happen.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🖥️ **Desktop GUI** | Modern dark-themed interface — no terminal needed |
| 📁 **Smart Classification** | Uses content signatures, not just file extensions |
| 📷 **EXIF-aware** | Sorts photos by date taken (year/month) |
| 🔄 **Deduplication** | Detects and skips exact duplicate files |
| ↩️ **Undo System** | Every move is logged in SQLite — instantly revert any operation |
| ⚡ **Dry Run Mode** | Preview where files *would* go before committing |
| 👁️ **File Watching** | Auto-organize files as they drop into a folder |
| 📝 **Custom Rules** | Define your own sorting rules via YAML config |

---

## 🚀 Quick Start

### Option 1: Download the Executable (Recommended)
1. Go to [**Releases**](https://github.com/Haruuowo/SmartSort/releases)
2. Download `SmartSort.exe`
3. Double-click to run — no installation needed!

### Option 2: Run from Source
```bash
# Clone the repo
git clone https://github.com/Haruuowo/SmartSort.git
cd SmartSort

# Install dependencies
pip install -r requirements.txt

# Launch the GUI
python tui.py
```

---

## 🖥️ Desktop App

The GUI features:
- **Browse** — Native Windows file picker to select any folder
- **Dry Run** — Simulate the sort to preview what will happen
- **Organize** — Execute the sort for real
- **Undo Last** — Revert the most recent operation
- **Stats Dashboard** — See totals, moved, skipped, and errors at a glance
- **Results Table** — Color-coded breakdown of every file processed

---

## 🛠️ CLI Usage

SmartSort also works as a command-line tool:

```bash
# Sort a folder
python -m smartsort sort "C:\Path\To\Folder"

# Watch a folder in real-time
python -m smartsort watch "C:\Path\To\Folder"

# Preview without moving files
python -m smartsort dry-run "C:\Path\To\Folder"

# Undo operations
python -m smartsort undo --limit 5
python -m smartsort undo --all
```

---

## ⚙️ Custom Rules

Edit `config/rules.yaml` to define your own sorting rules:

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

## 📂 Project Structure

```
SmartSort/
├── tui.py                  # Desktop GUI application
├── api.py                  # FastAPI backend (optional)
├── config/
│   └── rules.yaml          # Sorting rules configuration
├── smartsort/
│   ├── classifier.py       # Core file classification engine
│   ├── cli.py              # CLI interface (Typer)
│   ├── dedupe.py           # Duplicate detection
│   ├── history.py          # SQLite undo/history system
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

## 🧪 Running Tests

```bash
pytest tests/
```

---

## 🛡️ Tech Stack

- **Python 3.11** — Core logic
- **CustomTkinter** — Modern desktop GUI
- **SQLite** — Undo/history database
- **Pillow** — EXIF metadata extraction
- **filetype** — Content-based file detection
- **PyYAML** — Rule configuration
- **PyInstaller** — Executable packaging

---

<div align="center">

Made with 💜 by [Haruuowo](https://github.com/Haruuowo)

</div>
