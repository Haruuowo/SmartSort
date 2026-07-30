import os
import sys
import threading
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, END

from smartsort.classifier import FileClassifier
from smartsort.history import get_history, undo_move, init_db
from smartsort.cleaner import remove_empty_folders, find_empty_folders

def get_config_path() -> str:
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'config', 'rules.yaml')

# ── Aesthetic Color Palette (GitHub Dark / Neon Terminal) ──
BG           = "#090d16"
BG_CARD      = "#111827"
BG_INPUT     = "#1f2937"
BORDER       = "#374151"
TEXT_MAIN    = "#e5e7eb"
TEXT_MUTED   = "#9ca3af"

EMERALD      = "#10b981"
EMERALD_HOVER= "#059669"
CYAN         = "#38bdf8"
CYAN_HOVER   = "#0284c7"
AMBER        = "#f59e0b"
CRIMSON      = "#ef4444"
PURPLE       = "#a855f7"

FONT_MONO    = ("Consolas", 12)
FONT_MONO_SM = ("Consolas", 11)
FONT_MONO_LG = ("Consolas", 14, "bold")
FONT_TITLE   = ("Consolas", 20, "bold")


class SmartSortTerminal(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Window Settings ──
        self.title("SmartSort Terminal")
        self.geometry("860x620")
        self.minsize(720, 480)
        self.configure(fg_color=BG)
        ctk.set_appearance_mode("dark")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header Panel ──
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER)
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        header.grid_columnconfigure(1, weight=1)

        # Title & Subtitle
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=16, pady=12, sticky="w")

        ctk.CTkLabel(
            title_box, text="⚡ SmartSort",
            font=FONT_TITLE, text_color=EMERALD
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box, text="Intelligent File Organizer Terminal v1.0",
            font=FONT_MONO_SM, text_color=TEXT_MUTED
        ).pack(anchor="w")

        # Target Folder Input Box
        self.folder_var = ctk.StringVar(value="")
        self.folder_entry = ctk.CTkEntry(
            header, textvariable=self.folder_var,
            placeholder_text="Target directory path (click Browse or type)...",
            font=FONT_MONO_SM, height=36,
            fg_color=BG_INPUT, border_color=BORDER,
            text_color=CYAN, placeholder_text_color=TEXT_MUTED,
            corner_radius=6
        )
        self.folder_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=12)

        # Browse Button
        ctk.CTkButton(
            header, text="📁 Browse Folder", width=130, height=36,
            font=FONT_MONO_SM, fg_color=EMERALD, hover_color=EMERALD_HOVER,
            text_color="#ffffff", corner_radius=6,
            command=self.browse_folder
        ).grid(row=0, column=2, padx=(0, 14), pady=12)

        # ── Toolbar: Quick Action Buttons ──
        toolbar = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        toolbar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

        actions = [
            ("⚡ Dry Run", BG_INPUT, CYAN, lambda: self.run_sort(True)),
            ("🚀 Organize", EMERALD, "#ffffff", lambda: self.run_sort(False)),
            ("🗑️ Clean Empty", BG_INPUT, AMBER, self.cmd_clean_empty),
            ("↩ Undo Last", BG_INPUT, PURPLE, self.undo_last),
            ("📋 History", BG_INPUT, TEXT_MUTED, self.show_history),
            ("🧹 Clear Screen", BG_INPUT, TEXT_MUTED, self.clear_terminal),
            ("❓ Help", BG_INPUT, TEXT_MAIN, self.show_help),
        ]

        for text, bg, fg, cmd in actions:
            hover = EMERALD_HOVER if bg == EMERALD else BORDER
            btn = ctk.CTkButton(
                toolbar, text=text, width=105, height=32,
                font=FONT_MONO_SM, fg_color=bg, hover_color=hover,
                border_color=BORDER, border_width=1, corner_radius=6,
                text_color=fg, command=cmd
            )
            btn.pack(side="left", padx=3)

        # ── Terminal Output Screen ──
        terminal_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER)
        terminal_frame.grid(row=2, column=0, sticky="nsew", padx=14, pady=0)
        terminal_frame.grid_columnconfigure(0, weight=1)
        terminal_frame.grid_rowconfigure(0, weight=1)

        self.terminal = ctk.CTkTextbox(
            terminal_frame, font=FONT_MONO,
            fg_color=BG_CARD, text_color=TEXT_MAIN,
            border_width=0, corner_radius=8, wrap="word",
            activate_scrollbars=True,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=TEXT_MUTED
        )
        self.terminal.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.terminal.configure(state="disabled")

        # ── Command Prompt Bar ──
        prompt_bar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER)
        prompt_bar.grid(row=3, column=0, sticky="ew", padx=14, pady=12)
        prompt_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            prompt_bar, text="smartsort >",
            font=FONT_MONO_LG, text_color=EMERALD
        ).grid(row=0, column=0, padx=(14, 6), pady=8)

        self.cmd_input = ctk.CTkEntry(
            prompt_bar, font=FONT_MONO, fg_color=BG_CARD, text_color=TEXT_MAIN,
            border_width=0, corner_radius=0,
            placeholder_text="type command (sort, dry-run, browse, clean-empty, ls, history, undo, help)...",
            placeholder_text_color=TEXT_MUTED
        )
        self.cmd_input.grid(row=0, column=1, sticky="ew", pady=8)
        self.cmd_input.bind("<Return>", self._on_enter)

        # Print initial banner
        self.print_banner()

    def print_banner(self):
        banner = """
┌──────────────────────────────────────────────────────────────┐
│                    SMARTSORT TERMINAL                        │
│             Automated File Organization Engine               │
└──────────────────────────────────────────────────────────────┘
"""
        self._print(banner, EMERALD)
        self._print("[+] Click [📁 Browse Folder] above or type 'browse' to select a directory.", CYAN)
        self._print("[+] Type 'help' at the prompt to view full command documentation.\n", TEXT_MUTED)

    # ── Output Helpers ──
    def _print(self, text: str, color: str = TEXT_MAIN):
        self.terminal.configure(state="normal")
        tag = f"t{id(text)}_{os.urandom(4).hex()}"
        start = self.terminal.index("end-1c")
        self.terminal.insert(END, text + "\n")
        end = self.terminal.index("end-1c")
        self.terminal.tag_add(tag, start, end)
        self.terminal.tag_config(tag, foreground=color)
        self.terminal.see(END)
        self.terminal.configure(state="disabled")

    def clear_terminal(self):
        self.terminal.configure(state="normal")
        self.terminal.delete("1.0", END)
        self.terminal.configure(state="disabled")

    # ── Folder Picker ──
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        if folder:
            self.folder_var.set(folder)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self._print(f"\n[{timestamp}] [+] Target folder set: {folder}", CYAN)
            self._print(f"[{timestamp}]     Ready! Click [⚡ Dry Run] or [🚀 Organize].", TEXT_MUTED)

    # ── Command Prompt Dispatch ──
    def _on_enter(self, event):
        raw = self.cmd_input.get().strip()
        self.cmd_input.delete(0, END)
        if not raw:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        self._print(f"\n[{timestamp}] smartsort > {raw}", EMERALD)

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("help", "?"):
            self.show_help()
        elif cmd in ("sort", "run", "organize"):
            self.run_sort(dry_run=False, path_override=arg)
        elif cmd in ("dry-run", "dryrun", "sim"):
            self.run_sort(dry_run=True, path_override=arg)
        elif cmd in ("browse", "select"):
            self.browse_folder()
        elif cmd in ("clean-empty", "cleanempty", "clean", "rmdir"):
            self.cmd_clean_empty(arg)
        elif cmd == "ls":
            self._cmd_ls(arg)
        elif cmd == "history":
            self.show_history()
        elif cmd == "undo":
            self.undo_last(arg)
        elif cmd in ("clear", "cls"):
            self.clear_terminal()
        elif cmd == "pwd":
            self._print(os.getcwd(), CYAN)
        elif cmd in ("exit", "quit"):
            self.destroy()
        else:
            self._print(f"[-] Unknown command '{cmd}'. Type 'help' for available commands.", CRIMSON)

    def show_help(self):
        help_text = """
======================= COMMAND REFERENCE =======================
  sort [path]        Organize files in directory
  dry-run [path]     Simulate sort without moving files
  clean-empty [path] Detect and remove empty subfolders
  browse             Open Windows folder picker dialog
  ls [path]          List files in current or target directory
  history            Show recent move history
  undo [all]         Undo last move (or 'undo all' to revert all)
  clear              Clear terminal log screen
  pwd                Print current working directory
  exit               Exit SmartSort Terminal
=================================================================
"""
        self._print(help_text, AMBER)

    def _cmd_ls(self, path):
        target = path if path else (self.folder_var.get() or os.getcwd())
        if not os.path.isdir(target):
            self._print(f"[-] Directory not found: '{target}'", CRIMSON)
            return
        try:
            entries = sorted(os.listdir(target))
            self._print(f"Listing contents of {target}:", CYAN)
            for e in entries:
                full = os.path.join(target, e)
                if os.path.isdir(full):
                    self._print(f"  [DIR]  {e}/", CYAN)
                else:
                    size = os.path.getsize(full)
                    self._print(f"  [FILE] {e} ({self._format_size(size)})", TEXT_MAIN)
        except PermissionError:
            self._print("[-] Permission denied.", CRIMSON)

    def cmd_clean_empty(self, path_override: str = ""):
        folder = path_override if path_override else self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            folder = filedialog.askdirectory(title="Select Folder to Clean Empty Subfolders")
            if not folder:
                self._print("[-] No folder selected.", CRIMSON)
                return
            self.folder_var.set(folder)

        timestamp = datetime.now().strftime("%H:%M:%S")
        self._print(f"\n[{timestamp}] [*] Scanning for empty subdirectories in: {folder}", CYAN)
        removed = remove_empty_folders(folder, dry_run=False)

        if not removed:
            self._print(f"[{timestamp}] [!] No empty subdirectories found.", AMBER)
        else:
            for d in removed:
                self._print(f"  [REMOVED] Empty folder: {d}", CRIMSON)
            self._print(f"[{timestamp}] [✓] Cleaned {len(removed)} empty subfolder(s).\n", EMERALD)

    def run_sort(self, dry_run: bool, path_override: str = ""):
        folder = path_override if path_override else self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            folder = filedialog.askdirectory(title="Select Folder to Organize")
            if not folder:
                self._print("[-] Please select a valid folder.", CRIMSON)
                return
            self.folder_var.set(folder)

        config_path = get_config_path()
        if not os.path.exists(config_path):
            self._print(f"[-] Config file missing at: {config_path}", CRIMSON)
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        mode = "DRY RUN SIMULATION" if dry_run else "EXECUTING SORT"
        self._print(f"\n[{timestamp}] [*] Starting [{mode}] on: {folder}", AMBER if dry_run else EMERALD)
        self._print("─" * 64, TEXT_MUTED)

        threading.Thread(
            target=self._sort_worker, args=(folder, config_path, dry_run),
            daemon=True
        ).start()

    def _sort_worker(self, folder, config_path, dry_run):
        classifier = FileClassifier(folder, config_path)
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        except Exception as e:
            self.after(0, lambda: self._print(f"[-] Error accessing folder: {e}", CRIMSON))
            return

        if not files:
            self.after(0, lambda: self._print("[!] No files found to organize.", AMBER))
            return

        moved, duplicates, errors = 0, 0, 0

        for item in files:
            result = classifier.process_file(os.path.join(folder, item), dry_run=dry_run)
            status = result.get("status", "error")

            if status == "moved":
                moved += 1
                dest = os.path.basename(result.get("destination", ""))
                self.after(0, lambda i=item, d=dest: self._print(f"  [MOVED]     {i}  ──>  {d}", EMERALD))
            elif status == "duplicate":
                duplicates += 1
                dest = os.path.join("Duplicates", os.path.basename(result.get("destination", "")))
                self.after(0, lambda i=item, d=dest: self._print(f"  [DUPLICATE] {i}  ──>  {d}", AMBER))
            else:
                errors += 1
                r = result.get("reason", "Unknown")
                self.after(0, lambda i=item, r=r: self._print(f"  [ERROR]     {i}  ({r})", CRIMSON))

        total = len(files)

        def finish():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self._print("─" * 64, TEXT_MUTED)
            self._print(
                f"[{timestamp}] [✓] Complete! Moved: {moved} | Duplicates: {duplicates} | Errors: {errors} | Total: {total}\n",
                EMERALD if errors == 0 else AMBER
            )

        self.after(0, finish)

    def show_history(self):
        try:
            records = get_history(15)
        except Exception as e:
            self._print(f"[-] History error: {e}", CRIMSON)
            return

        if not records:
            self._print("[!] No move history recorded.", AMBER)
            return

        self._print("\n=== RECENT MOVE HISTORY ===", PURPLE)
        for r in records:
            self._print(f"  #{r[0]} | {os.path.basename(r[1])} ──> {os.path.basename(r[2])} [{r[3]}]", TEXT_MAIN)
        self._print("===========================\n", PURPLE)

    def undo_last(self, arg: str = ""):
        try:
            records = get_history(None if arg.lower() == "all" else 1)
        except Exception as e:
            self._print(f"[-] Undo error: {e}", CRIMSON)
            return

        if not records:
            self._print("[!] Nothing to undo.", AMBER)
            return

        for record in records:
            name = os.path.basename(record[1])
            if undo_move(record):
                self._print(f"  [UNDONE] Restored: {name}", EMERALD)
            else:
                self._print(f"  [FAILED] Could not restore: {name}", CRIMSON)

    @staticmethod
    def _format_size(b: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"


if __name__ == "__main__":
    init_db()
    app = SmartSortTerminal()
    app.mainloop()
