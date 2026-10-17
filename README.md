<div align="center">

<img src="web/SS_1.png" alt="SmartSort Logo" width="96" height="96" style="border-radius: 20px; box-shadow: 0 10px 30px rgba(217, 70, 239, 0.35);" />

# SmartSort

**The intelligent, safety-first desktop file organizer for Windows.**  
*Clean up messy Downloads, sort photos by EXIF capture date, and manage disk storage in seconds.*

[![Release](https://img.shields.io/github/v/release/Haruuowo/Projects?style=for-the-badge&color=8b5cf6&label=Version)](https://github.com/Haruuowo/Projects/releases)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Haruuowo/Projects)
[![License](https://img.shields.io/badge/License-MIT-34d399?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-10b981?style=for-the-badge&logo=pytest&logoColor=white)](tests/)

<br />

[**Download SmartSort.exe**](https://github.com/Haruuowo/Projects/releases) • [**Quick Start**](#-quick-start) • [**Features**](#-key-features) • [**Custom Rules**](#-custom-sorting-rules) • [**Tech Stack**](#-tech-stack)

</div>

---

## ⚡ What is SmartSort?

Every computer has a messy folder — usually `Downloads` or `Desktop` — filled with hundreds of loose PDFs, screenshots, installers, video clips, and duplicate files.

**SmartSort** is a modern desktop utility built to solve this once and for all:
1. **Choose a folder** — SmartSort scans loose files and inspects subfolder sizes across all CPU threads.
2. **Review the Preview** — Inspect collapsible destination groups to see *exactly* where every file will go. No surprises.
3. **Organize or Undo** — Click **Organize** to sort files instantly. Changed your mind? Revert the entire run with **1-click Atomic Undo**.

> **Safety First:** SmartSort never deletes your files. Exact duplicates are moved into a dedicated `Duplicates` folder, system/temporary files are left untouched, and file name collisions automatically receive a clean counter `(1)` without overwriting.

---

## ✨ Key Features

<table>
  <tr>
    <td width="50%">
      <h3>🛡️ Safety-First Preview Mode</h3>
      Files are never moved blindly. Browse interactive, expandable category cards showing destination folders, file counts, and duplicate flags before applying changes.
    </td>
    <td width="50%">
      <h3>⏪ 1-Click Atomic Batch Undo</h3>
      Every organize run is logged as an atomic transaction in SQLite (WAL mode). Revert an entire run of 10,000+ files in seconds with automatic empty directory cleanup.
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🚀 Ultra-Fast C-Level Win32 Scanner</h3>
      Direct Windows Kernel32 integration scans massive drives and folders across CPU cores. Inspect storage breakdowns, top largest files, and subfolder size shares instantly.
    </td>
    <td width="50%">
      <h3>🔍 O(N) Indexed Deduplication</h3>
      Fast SHA-256 and size-indexed duplicate detection isolates exact file duplicates into a separate <code>Duplicates</code> folder for easy review without data loss.
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>📷 EXIF Photo Organization</h3>
      SmartSort extracts camera metadata from JPG, PNG, WEBP, and HEIC photos to automatically organize them into date hierarchies: <code>Photos/{year}/{month}</code>.
    </td>
    <td width="50%">
      <h3>🖱️ WizTree-Style File Management</h3>
      Right-click any file or subfolder in the scanner tables to <b>Reveal in File Explorer</b>, <b>Copy Full Path</b>, or <b>Send to Recycle Bin</b>.
    </td>
  </tr>
</table>

---

## 📸 Interface Preview

<div align="center">

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  SmartSort                                                  [ _ ] [ 口 ] [ X ]   │
├─────────────┬────────────────────────────────────────────────────────────────────┤
│  OVERVIEW   │  Target: C:\Users\Worldwide\Downloads            [ Choose Folder ] │
│  ORGANIZE   ├────────────────────────────────────────────────────────────────────┤
│  HISTORY    │  [ 142 Loose Files ]  [ 4.8 GB Total ]  [ 12 Subfolders ]          │
│  RULES      ├────────────────────────────────────────────────────────────────────┤
│  HELP       │  Storage Composition:                                              │
│             │  [████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] │
│             │  ■ Images (2.1 GB)  ■ Documents (1.2 GB)  ■ Installers (980 MB)    │
│             ├────────────────────────────────────────────────────────────────────┤
│             │  Preview Plan:                                                     │
│             │  📁 Images/Screenshots/   (34 files · 180 MB)                [ v ] │
│             │  📁 Documents/            (52 files · 1.2 GB)                [ v ] │
│             │  📁 Photos/2026/10/       (28 files · 720 MB)                [ v ] │
│             │  📁 Duplicates/           (8 duplicates detected)            [ v ] │
│             ├────────────────────────────────────────────────────────────────────┤
│             │                                           [  Organize 142 Files  ] │
└─────────────┴────────────────────────────────────────────────────────────────────┘
```

</div>

---

## 🚀 Quick Start

### Option 1: Standalone Executable (Recommended)
No installation or Python environment required:
1. Head to [**Releases**](https://github.com/Haruuowo/Projects/releases)
2. Download `SmartSort.exe`
3. Double-click to launch!

> **Note on Windows SmartScreen ("Windows protected your PC"):**  
> Because SmartSort is an independent open-source project and does not possess an expensive commercial code-signing certificate (~$400/year), Microsoft Defender SmartScreen may display an *"Unrecognized app"* prompt on brand new releases.  
> Simply click **More info** ➔ **Run anyway**. SmartSort is 100% open-source, and you can audit the source code right here.

### Option 2: Run from Source
```bash
# 1. Clone the repository
git clone https://github.com/Haruuowo/Projects.git
cd Projects

# 2. Set up virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch SmartSort
python Organizer.py
```

---

## ⚙️ Custom Sorting Rules

Customize and add rules easily via `config/rules.yaml`. Rules are evaluated from top to bottom:

```yaml
rules:
  # Route bills and invoices
  - name: "Receipts & Invoices"
    condition:
      name_contains: ["receipt", "invoice", "bill", "tax", "statement"]
    destination: "Finance/Receipts"

  # Capture screenshots
  - name: "Screenshots"
    condition:
      name_contains: ["screenshot", "screen_shot", "capture"]
    destination: "Images/Screenshots"

  # Camera photos sorted by EXIF date
  - name: "Photos with EXIF"
    condition:
      extensions: [".png", ".jpg", ".jpeg", ".heic"]
      has_exif_date: true
    destination: "Photos/{year}/{month}"

  # Documents
  - name: "Documents"
    condition:
      extensions: [".pdf", ".docx", ".xlsx", ".pptx", ".txt"]
    destination: "Documents"

  # Development code
  - name: "Code"
    condition:
      extensions: [".py", ".js", ".ts", ".html", ".css", ".json", ".sql"]
    destination: "Code"
```

---

## 📂 Project Architecture

```
SmartSort/
├── Organizer.py            # Primary desktop entry point
├── webview_app.py          # PyWebView desktop launcher & native bridge
├── server.py               # Local non-blocking HTTP API server
├── config/
│   └── rules.yaml          # YAML sorting rules configuration
├── web/                    # Dashboard UI assets (HTML5 / Vanilla CSS / ES6)
│   ├── index.html          # Lightweight UI shell
│   ├── style.css           # Slate dark design system & tokens
│   ├── app.js              # State controller, progress tracker & undo
│   └── SS_1.png            # Application logo
├── smartsort/
│   ├── analyzer.py         # Win32 C-API parallel folder scanner
│   ├── classifier.py       # Plan & organize engine
│   ├── dedupe.py           # O(N) indexed SHA-256 duplicate detection
│   ├── history.py          # Atomic SQLite undo transaction system
│   ├── cleaner.py          # Empty directory recursive cleaner
│   ├── rules.py            # Rule engine with pre-compiled matchers
│   └── watcher.py          # Real-time directory filesystem watcher
├── tests/
│   ├── test_classifier.py  # Classifier & plan tests
│   ├── test_history.py     # Batched undo & collision tests
│   ├── test_dedupe.py      # Duplicate detection tests
│   └── test_rules.py       # Rule engine tests
├── SmartSort.spec          # PyInstaller standalone build specification
└── requirements.txt        # Python package dependencies
```

---

## 🛠️ Tech Stack

* **Language**: Python 3.9+ (Windows Kernel32 C-API bindings)
* **Desktop Wrapper**: [PyWebView](https://pywebview.flowrl.com/) + native WebView2
* **Storage Engine**: SQLite 3 with Write-Ahead Logging (`WAL`)
* **Metadata & Types**: Pillow (EXIF Date extraction) & `filetype` (Magic bytes detection)
* **Configuration**: PyYAML
* **Testing**: Pytest

---

## 🧪 Testing

Run the automated test suite:

```bash
pytest -v
```

All 10 unit tests for deduplication, batched undo, rules evaluation, and classifier execution pass with zero errors.

---


<div align="center">

Crafted with care by [**Doton, John Harold**](https://github.com/Haruuowo)

</div>
