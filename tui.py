import os
import sys
import threading
import customtkinter as ctk
from tkinter import filedialog, END

from smartsort.classifier import FileClassifier
from smartsort.history import get_history, undo_move, init_db

def get_config_path() -> str:
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'config', 'rules.yaml')

# ── Terminal Theme Colors ──
BG          = "#0d1117"
BG_SECONDARY= "#161b22"
BG_INPUT    = "#21262d"
TEXT_MAIN   = "#c9d1d9"
GREEN       = "#3fb950"
CYAN        = "#58a6ff"
YELLOW      = "#d29922"
RED         = "#f85149"
PURPLE      = "#bc8cff"
GRAY        = "#8b949e"

FONT_MONO    = ("Consolas", 12)
FONT_MONO_SM = ("Consolas", 11)
FONT_MONO_LG = ("Consolas", 14, "bold")
FONT_TITLE   = ("Consolas", 18, "bold")


class SmartSortTerminal(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Standard App Window ──
        self.title("SmartSort")
        self.geometry("820x580")
        self.minsize(700, 450)
        self.configure(fg_color=BG)
        ctk.set_appearance_mode("dark")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Top Bar: Title & Direct Folder Selector ──
        top_bar = ctk.CTkFrame(self, fg_color=BG_SECONDARY, corner_radius=6, border_width=1, border_color="#30363d")
        top_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        top_bar.grid_columnconfigure(1, weight=1)

        # App Title
        ctk.CTkLabel(
            top_bar, text="SmartSort",
            font=FONT_TITLE, text_color=GREEN
        ).grid(row=0, column=0, padx=14, pady=10)

        # Folder Input Display
        self.folder_var = ctk.StringVar(value="")
        self.folder_entry = ctk.CTkEntry(
            top_bar, textvariable=self.folder_var,
            placeholder_text="No folder selected — click [Select Folder] or type path...",
            font=FONT_MONO_SM, height=34,
            fg_color=BG_INPUT, border_color="#30363d",
            text_color=CYAN, placeholder_text_color=GRAY,
            corner_radius=4
        )
        self.folder_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=10)

        # Select Folder Button (Direct Link File Picker)
        ctk.CTkButton(
            top_bar, text="📂 Select Folder", width=120, height=34,
            font=FONT_MONO_SM, fg_color="#238636", hover_color="#2ea043",
            text_color="#ffffff", corner_radius=4,
            command=self.browse_folder
        ).grid(row=0, column=2, padx=(0, 10), pady=10)

        # ── Quick Action Buttons Bar ──
        actions_bar = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        actions_bar.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))

        buttons = [
            ("⚡ Dry Run", BG_INPUT, CYAN, lambda: self.run_sort(True)),
            ("🚀 Organize", BG_INPUT, GREEN, lambda: self.run_sort(False)),
            ("↩ Undo Last", BG_INPUT, YELLOW, self.undo_last),
            ("📋 History", BG_INPUT, PURPLE, self.show_history),
            ("🧹 Clear", BG_INPUT, GRAY, self.clear_terminal),
            ("❓ Help", BG_INPUT, TEXT_MAIN, self.show_help),
        ]
        for text, bg, fg, cmd in buttons:
            ctk.CTkButton(
                actions_bar, text=text, width=105, height=30,
                font=FONT_MONO_SM, fg_color=bg, hover_color="#30363d",
                border_color="#30363d", border_width=1, corner_radius=4,
                text_color=fg, command=cmd
            ).pack(side="left", padx=3)

        # ── Terminal Output Screen ──
        output_frame = ctk.CTkFrame(self, fg_color=BG_SECONDARY, corner_radius=6, border_width=1, border_color="#30363d")
        output_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=0)
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(0, weight=1)

        self.terminal = ctk.CTkTextbox(
            output_frame, font=FONT_MONO,
            fg_color=BG_SECONDARY, text_color=TEXT_MAIN,
            border_width=0, corner_radius=6, wrap="word",
            activate_scrollbars=True,
            scrollbar_button_color="#30363d",
            scrollbar_button_hover_color=GRAY
        )
        self.terminal.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.terminal.configure(state="disabled")

        # ── Command Prompt Input Line ──
        prompt_frame = ctk.CTkFrame(self, fg_color=BG_SECONDARY, corner_radius=6, border_width=1, border_color="#30363d")
        prompt_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=10)
        prompt_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            prompt_frame, text="SmartSort >",
            font=FONT_MONO_LG, text_color=GREEN
        ).grid(row=0, column=0, padx=(12, 6), pady=6)

        self.cmd_input = ctk.CTkEntry(
            prompt_frame, font=FONT_MONO, fg_color=BG_SECONDARY, text_color=TEXT_MAIN,
            border_width=0, corner_radius=0,
            placeholder_text="type a command (sort, dry-run, browse, ls, history, undo, help)...",
            placeholder_text_color=GRAY
        )
        self.cmd_input.grid(row=0, column=1, sticky="ew", pady=6)
        self.cmd_input.bind("<Return>", self._on_enter)

        # ── Initial Greeting ──
        self.print_banner()

    def print_banner(self):
        banner = """
================================================================
                       SmartSort v1.0                           
               Intelligent File Organizer Tool                  
================================================================
"""
        self._print(banner, GREEN)
        self._print("Click [📂 Select Folder] above or type commands below.", CYAN)
        self._print("Type 'help' to see full command list.\n", GRAY)

    # ── Printing Helpers ──
    def _print(self, text, color=TEXT_MAIN):
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
            self._print(f"\n[+] Selected folder: {folder}", CYAN)
            self._print("    Click [⚡ Dry Run] to test, or [🚀 Organize] to sort.", GRAY)

    # ── Command Prompt Execution ──
    def _on_enter(self, event):
        raw = self.cmd_input.get().strip()
        self.cmd_input.delete(0, END)
        if not raw:
            return

        self._print(f"\nSmartSort > {raw}", GREEN)

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "help":
            self.show_help()
        elif cmd in ("sort", "run"):
            self.run_sort(dry_run=False, path_override=arg)
        elif cmd in ("dry-run", "dryrun", "sim"):
            self.run_sort(dry_run=True, path_override=arg)
        elif cmd in ("browse", "select"):
            self.browse_folder()
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
            self._print(f"[-] Unknown command '{cmd}'. Type 'help' for options.", RED)

    def show_help(self):
        help_text = """
--------------------- COMMANDS MENU ---------------------
  sort [path]       Organize all files in directory
  dry-run [path]    Simulate sort without moving files
  browse            Open Windows folder picker dialog
  ls [path]         List files in current or target folder
  history           Show history of recent file moves
  undo              Undo the last file move operation
  undo all          Undo all recorded file moves
  clear             Clear screen output
  pwd               Print current working directory
  exit              Quit SmartSort
---------------------------------------------------------
"""
        self._print(help_text, YELLOW)

    def _cmd_ls(self, path):
        target = path if path else (self.folder_var.get() or os.getcwd())
        if not os.path.isdir(target):
            self._print(f"[-] Invalid directory: '{target}'", RED)
            return
        try:
            entries = sorted(os.listdir(target))
            self._print(f"Listing {target}:", CYAN)
            for e in entries:
                full = os.path.join(target, e)
                if os.path.isdir(full):
                    self._print(f"  [DIR]  {e}/", CYAN)
                else:
                    size = os.path.getsize(full)
                    self._print(f"  [FILE] {e} ({self._format_size(size)})", TEXT_MAIN)
        except PermissionError:
            self._print("[-] Permission denied.", RED)

    def run_sort(self, dry_run: bool, path_override: str = ""):
        folder = path_override if path_override else self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            # Prompt user to browse if no path is provided
            folder = filedialog.askdirectory(title="Select Folder to Organize")
            if not folder:
                self._print("[-] Please select a valid folder.", RED)
                return
            self.folder_var.set(folder)

        config_path = get_config_path()
        if not os.path.exists(config_path):
            self._print(f"[-] Config file not found at: {config_path}", RED)
            return

        mode = "DRY RUN SIMULATION" if dry_run else "EXECUTING SORT"
        self._print(f"\n[*] Starting [{mode}] on: {folder}", YELLOW if dry_run else GREEN)
        self._print("----------------------------------------------------------------", GRAY)

        threading.Thread(
            target=self._sort_worker, args=(folder, config_path, dry_run),
            daemon=True
        ).start()

    def _sort_worker(self, folder, config_path, dry_run):
        classifier = FileClassifier(folder, config_path)
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        except Exception as e:
            self.after(0, lambda: self._print(f"[-] Error reading folder: {e}", RED))
            return

        if not files:
            self.after(0, lambda: self._print("[!] No files found to organize.", YELLOW))
            return

        moved, skipped, errors = 0, 0, 0

        for item in files:
            result = classifier.process_file(os.path.join(folder, item), dry_run=dry_run)
            status = result.get("status", "error")

            if status == "moved":
                moved += 1
                dest = os.path.basename(result.get("destination", ""))
                self.after(0, lambda i=item, d=dest: self._print(f"  [MOVED]     {i}  -->  {d}", GREEN))
            elif status == "duplicate":
                skipped += 1
                r = result.get("reason", "")
                self.after(0, lambda i=item, r=r: self._print(f"  [SKIPPED]   {i}  ({r})", YELLOW))
            else:
                errors += 1
                r = result.get("reason", "Unknown")
                self.after(0, lambda i=item, r=r: self._print(f"  [ERROR]     {i}  ({r})", RED))

        total = len(files)

        def finish():
            self.after(0, lambda: self._print("----------------------------------------------------------------", GRAY))
            self.after(0, lambda: self._print(
                f"[✓] Complete! Moved: {moved} | Skipped: {skipped} | Errors: {errors} | Total: {total}\n",
                GREEN if errors == 0 else YELLOW
            ))

        finish()

    def show_history(self):
        try:
            records = get_history(15)
        except Exception as e:
            self._print(f"[-] History error: {e}", RED)
            return

        if not records:
            self._print("[!] No move history found.", YELLOW)
            return

        self._print("\n=== Recent Move History ===", PURPLE)
        for r in records:
            self._print(f"  #{r[0]} | {os.path.basename(r[1])} --> {os.path.basename(r[2])} [{r[3]}]", TEXT_MAIN)
        self._print("===========================\n", PURPLE)

    def undo_last(self, arg: str = ""):
        try:
            records = get_history(None if arg.lower() == "all" else 1)
        except Exception as e:
            self._print(f"[-] Undo error: {e}", RED)
            return

        if not records:
            self._print("[!] Nothing to undo.", YELLOW)
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
