import os
import sys
import threading
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, END

from smartsort.classifier import FileClassifier
from smartsort.history import get_history, undo_move, init_db
from smartsort.cleaner import remove_empty_folders, find_empty_folders
from smartsort.analyzer import analyze_directory, format_size as fmt_size, generate_bar

def get_config_path() -> str:
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'config', 'rules.yaml')

# ── Minimal Terminal Color Palette (Clean Dark Mode) ──
BG           = "#121212"
BG_CARD      = "#1c1c1c"
BG_INPUT     = "#242424"
BORDER       = "#333333"

TEXT_MAIN    = "#d4d4d4"
TEXT_MUTED   = "#757575"

GREEN        = "#4caf50"
GREEN_HOVER  = "#388e3c"
BLUE         = "#64b5f6"
AMBER        = "#ffb74d"
RED          = "#e57373"
PURPLE       = "#b388ff"

FONT_MONO    = ("Consolas", 12)
FONT_MONO_SM = ("Consolas", 11)
FONT_MONO_LG = ("Consolas", 13, "bold")
FONT_TITLE   = ("Consolas", 18, "bold")

BANNER_ASCII = r"""
  ███████╗███╗   ███╗█████╗ ██████╗ ████████╗███████╗██████╗ ██████╗ ████████╗
  ██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗██╔══██╗╚══██╔══╝
  ███████╗██╔████╔██║███████║██████╔╝   ██║   ███████╗██║  ██║██████╔╝   ██║   
  ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║   ╚════██║██║  ██║██╔══██╗   ██║   
  ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   ███████║╚██████╔╝██║  ██║   ██║   
  ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
"""


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
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=6, border_width=1, border_color=BORDER)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        header.grid_columnconfigure(1, weight=1)

        # Title & Subtitle
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=14, pady=10, sticky="w")

        ctk.CTkLabel(
            title_box, text="# SMARTSORT",
            font=FONT_TITLE, text_color=GREEN
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box, text="[v1.2.0] File Organization Terminal Engine",
            font=FONT_MONO_SM, text_color=TEXT_MUTED
        ).pack(anchor="w")

        # Target Folder Input Box
        self.folder_var = ctk.StringVar(value="")
        self.folder_entry = ctk.CTkEntry(
            header, textvariable=self.folder_var,
            placeholder_text="Target directory path (click Browse or type)...",
            font=FONT_MONO_SM, height=34,
            fg_color=BG_INPUT, border_color=BORDER,
            text_color=BLUE, placeholder_text_color=TEXT_MUTED,
            corner_radius=4
        )
        self.folder_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)

        # Browse Folder Button
        ctk.CTkButton(
            header, text="[ Browse Folder ]", width=130, height=34,
            font=FONT_MONO_SM, fg_color=GREEN, hover_color=GREEN_HOVER,
            text_color="#ffffff", corner_radius=4,
            command=self.browse_folder
        ).grid(row=0, column=2, padx=(0, 14), pady=10)

        # ── Toolbar: Action Buttons ──
        toolbar = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        toolbar.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))

        actions = [
            ("[ Scan ]", BG_CARD, BLUE, self.cmd_scan),
            ("[ Top Files ]", BG_CARD, BLUE, self.cmd_top_files),
            ("[ Dry Run ]", BG_CARD, BLUE, lambda: self.run_sort(True)),
            ("[ Organize ]", GREEN, "#ffffff", lambda: self.run_sort(False)),
            ("[ Clean Empty ]", BG_CARD, AMBER, self.cmd_clean_empty),
            ("[ Undo Last ]", BG_CARD, PURPLE, self.undo_last),
            ("[ History ]", BG_CARD, TEXT_MUTED, self.show_history),
            ("[ Clear ]", BG_CARD, TEXT_MUTED, self.clear_terminal),
            ("[ Help ]", BG_CARD, TEXT_MAIN, self.show_help),
        ]

        for text, bg, fg, cmd in actions:
            hover = GREEN_HOVER if bg == GREEN else BORDER
            btn = ctk.CTkButton(
                toolbar, text=text, width=90, height=30,
                font=FONT_MONO_SM, fg_color=bg, hover_color=hover,
                border_color=BORDER, border_width=1, corner_radius=4,
                text_color=fg, command=cmd
            )
            btn.pack(side="left", padx=2)

        # ── Terminal Output Screen ──
        terminal_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=6, border_width=1, border_color=BORDER)
        terminal_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=0)
        terminal_frame.grid_columnconfigure(0, weight=1)
        terminal_frame.grid_rowconfigure(0, weight=1)

        self.terminal = ctk.CTkTextbox(
            terminal_frame, font=FONT_MONO,
            fg_color=BG_CARD, text_color=TEXT_MAIN,
            border_width=0, corner_radius=6, wrap="word",
            activate_scrollbars=True,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=TEXT_MUTED
        )
        self.terminal.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.terminal.configure(state="disabled")

        # ── Command Prompt Bar ──
        prompt_bar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=6, border_width=1, border_color=BORDER)
        prompt_bar.grid(row=3, column=0, sticky="ew", padx=12, pady=10)
        prompt_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            prompt_bar, text="smartsort >",
            font=FONT_MONO_LG, text_color=GREEN
        ).grid(row=0, column=0, padx=(12, 6), pady=6)

        self.cmd_input = ctk.CTkEntry(
            prompt_bar, font=FONT_MONO, fg_color=BG_CARD, text_color=TEXT_MAIN,
            border_width=0, corner_radius=0,
            placeholder_text="type command (sort, dry-run, browse, clean-empty, ls, history, undo, help)...",
            placeholder_text_color=TEXT_MUTED
        )
        self.cmd_input.grid(row=0, column=1, sticky="ew", pady=6)
        self.cmd_input.bind("<Return>", self._on_enter)

        # Print initial banner
        self.print_banner()

    def print_banner(self):
        self._print(BANNER_ASCII, GREEN)
        self._print("  [+] Click [ Browse Folder ] or type 'browse' to select target directory.", BLUE)
        self._print("  [+] Type 'help' at the prompt to view full command documentation.\n", TEXT_MUTED)

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
        self.print_banner()

    # ── Folder Picker ──
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        if folder:
            self.folder_var.set(folder)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self._print(f"\n[{timestamp}] [+] Target directory set: {folder}", BLUE)
            self._print(f"[{timestamp}]     Ready! Click [ Dry Run ] or [ Organize ].", TEXT_MUTED)

    # ── Command Prompt Dispatch ──
    def _on_enter(self, event):
        raw = self.cmd_input.get().strip()
        self.cmd_input.delete(0, END)
        if not raw:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        self._print(f"\n[{timestamp}] smartsort > {raw}", GREEN)

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("help", "?"):
            self.show_help()
        elif cmd in ("scan", "analyze"):
            self.cmd_scan(arg)
        elif cmd in ("top-files", "topfiles", "largest"):
            self.cmd_top_files(arg)
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
            self._print(os.getcwd(), BLUE)
        elif cmd in ("exit", "quit"):
            self.destroy()
        else:
            self._print(f"[-] Unknown command '{cmd}'. Type 'help' for available commands.", RED)

    def show_help(self):
        help_text = """
======================= COMMAND REFERENCE =======================
  scan [path]        WizTree-style category & size breakdown
  top-files [path]   Show 10 largest files in directory
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

    def cmd_scan(self, path_override: str = ""):
        folder = path_override if path_override else self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            folder = filedialog.askdirectory(title="Select Folder to Scan")
            if not folder:
                self._print("[-] No folder selected.", RED)
                return
            self.folder_var.set(folder)

        config_path = get_config_path()
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._print(f"\n[{timestamp}] [*] Scanning folder (WizTree Breakdown): {folder}", BLUE)
        self._print("────────────────────────────────────────────────────────────────", TEXT_MUTED)

        summary = analyze_directory(folder, config_path)
        total_size = summary['total_size']
        total_files = summary['total_files']

        if total_files == 0:
            self._print("[!] Folder is empty.", AMBER)
            return

        self._print(f"Total Folder Size: {fmt_size(total_size)} ({total_files} files)\n", GREEN)
        self._print(f"  {'CATEGORY':<18} {'FILES':<8} {'SIZE':<10} {'% SIZE':<8} VISUAL DISTRIBUTION", TEXT_MUTED)
        self._print(f"  {'─'*18} {'─'*8} {'─'*10} {'─'*8} {'─'*22}", TEXT_MUTED)

        sorted_cats = sorted(summary['categories'].items(), key=lambda x: x[1]['size'], reverse=True)
        for cat, data in sorted_cats:
            count = data['count']
            size = data['size']
            pct = (size / total_size * 100.0) if total_size > 0 else 0.0
            bar = generate_bar(pct, width=16)
            self._print(f"  {cat:<18} {count:<8} {fmt_size(size):<10} {pct:5.1f}%   [{bar}]", TEXT_MAIN)

        self._print("────────────────────────────────────────────────────────────────\n", TEXT_MUTED)

    def cmd_top_files(self, path_override: str = ""):
        folder = path_override if path_override else self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            folder = filedialog.askdirectory(title="Select Folder to Find Largest Files")
            if not folder:
                self._print("[-] No folder selected.", RED)
                return
            self.folder_var.set(folder)

        config_path = get_config_path()
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._print(f"\n[{timestamp}] [*] Top 10 Largest Files in: {folder}", BLUE)
        self._print("────────────────────────────────────────────────────────────────", TEXT_MUTED)

        summary = analyze_directory(folder, config_path)
        top_files = summary['top_files']

        if not top_files:
            self._print("[!] No files found.", AMBER)
            return

        for i, item in enumerate(top_files, 1):
            name = item['name']
            size_str = fmt_size(item['size'])
            cat = item['category']
            self._print(f"  #{i:<2} {size_str:<10}  {name}  --> ({cat})", TEXT_MAIN)

        self._print("────────────────────────────────────────────────────────────────\n", TEXT_MUTED)

    def _cmd_ls(self, path):
        target = path if path else (self.folder_var.get() or os.getcwd())
        if not os.path.isdir(target):
            self._print(f"[-] Directory not found: '{target}'", RED)
            return
        try:
            entries = sorted(os.listdir(target))
            self._print(f"Listing contents of {target}:", BLUE)
            for e in entries:
                full = os.path.join(target, e)
                if os.path.isdir(full):
                    self._print(f"  [DIR]  {e}/", BLUE)
                else:
                    size = os.path.getsize(full)
                    self._print(f"  [FILE] {e} ({self._format_size(size)})", TEXT_MAIN)
        except PermissionError:
            self._print("[-] Permission denied.", RED)

    def cmd_clean_empty(self, path_override: str = ""):
        folder = path_override if path_override else self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            folder = filedialog.askdirectory(title="Select Folder to Clean Empty Subfolders")
            if not folder:
                self._print("[-] No folder selected.", RED)
                return
            self.folder_var.set(folder)

        timestamp = datetime.now().strftime("%H:%M:%S")
        self._print(f"\n[{timestamp}] [*] Scanning for empty subdirectories in: {folder}", BLUE)
        removed = remove_empty_folders(folder, dry_run=False)

        if not removed:
            self._print(f"[{timestamp}] [!] No empty subdirectories found.", AMBER)
        else:
            for d in removed:
                self._print(f"  [REMOVED] Empty folder: {d}", RED)
            self._print(f"[{timestamp}] [+] Cleaned {len(removed)} empty subfolder(s).\n", GREEN)

    def run_sort(self, dry_run: bool, path_override: str = ""):
        folder = path_override if path_override else self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            folder = filedialog.askdirectory(title="Select Folder to Organize")
            if not folder:
                self._print("[-] Please select a valid folder.", RED)
                return
            self.folder_var.set(folder)

        config_path = get_config_path()
        if not os.path.exists(config_path):
            self._print(f"[-] Config file missing at: {config_path}", RED)
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        mode = "DRY RUN SIMULATION" if dry_run else "EXECUTING SORT"
        self._print(f"\n[{timestamp}] [*] Starting [{mode}] on: {folder}", AMBER if dry_run else GREEN)
        self._print("────────────────────────────────────────────────────────────────", TEXT_MUTED)

        threading.Thread(
            target=self._sort_worker, args=(folder, config_path, dry_run),
            daemon=True
        ).start()

    def _sort_worker(self, folder, config_path, dry_run):
        classifier = FileClassifier(folder, config_path)
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        except Exception as e:
            self.after(0, lambda: self._print(f"[-] Error accessing folder: {e}", RED))
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
                self.after(0, lambda i=item, d=dest: self._print(f"  [MOVED]     {i}  ──>  {d}", GREEN))
            elif status == "duplicate":
                duplicates += 1
                dest = os.path.join("Duplicates", os.path.basename(result.get("destination", "")))
                self.after(0, lambda i=item, d=dest: self._print(f"  [DUPLICATE] {i}  ──>  {d}", AMBER))
            else:
                errors += 1
                r = result.get("reason", "Unknown")
                self.after(0, lambda i=item, r=r: self._print(f"  [ERROR]     {i}  ({r})", RED))

        total = len(files)

        def finish():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self._print("────────────────────────────────────────────────────────────────", TEXT_MUTED)
            self._print(
                f"[{timestamp}] [+] Complete! Moved: {moved} | Duplicates: {duplicates} | Errors: {errors} | Total: {total}\n",
                GREEN if errors == 0 else AMBER
            )

        self.after(0, finish)

    def show_history(self):
        try:
            records = get_history(15)
        except Exception as e:
            self._print(f"[-] History error: {e}", RED)
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
            self._print(f"[-] Undo error: {e}", RED)
            return

        if not records:
            self._print("[!] Nothing to undo.", AMBER)
            return

        for record in records:
            name = os.path.basename(record[1])
            if undo_move(record):
                self._print(f"  [UNDONE] Restored: {name}", GREEN)
            else:
                self._print(f"  [FAILED] Could not restore: {name}", RED)

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
