<div align="center">

# SmartSort

**An intelligent, rule-based file organizer with a modern desktop dashboard UI.**

Built with Python · PyWebView · HTML/CSS/JS · SQLite

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Haruuowo/SmartSort)

</div>

---

## What is SmartSort?

SmartSort is a desktop application that organizes your files into categorized folders. It uses content-based detection (not just file extensions), custom YAML rules, EXIF metadata for photos, and built-in deduplication — wrapped in a sleek modern desktop dashboard.

> No more manually sorting your Downloads folder. Point SmartSort at a directory, click **Organize**, and it handles the rest.

---

## Features

| Feature | Description |
|---|---|
| Modern Desktop Dashboard | Sleek web-based UI wrapped in PyWebView |
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
python Organizer.py
```

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
├── Organizer.py            # Main App Entry Point
├── webview_app.py          # PyWebView Launcher
├── server.py               # Local HTTP API Server
├── config/
│   └── rules.yaml          # Sorting rules
├── web/                    # Dashboard UI Assets
│   ├── index.html
│   ├── style.css
│   └── app.js
├── smartsort/
│   ├── classifier.py       # File classification engine
│   ├── dedupe.py           # Duplicate detection
│   ├── history.py          # SQLite undo system
│   ├── rules.py            # YAML rule engine
│   └── watcher.py          # Real-time file watcher
├── tests/
│   ├── test_dedupe.py
│   └── test_rules.py
└── requirements.txt
```

---

## Tech Stack

- **Python 3.11** — Core logic & API server
- **PyWebView + HTML/CSS/JS** — Modern Desktop Dashboard UI
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
