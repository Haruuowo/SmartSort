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

# ── Theme ──
BG       = "#1e1e1e"
BG_BAR   = "#2d2d2d"
FG       = "#d4d4d4"
GREEN    = "#4ec359"
YELLOW   = "#e5c07b"
RED      = "#e06c75"
CYAN     = "#56b6c2"
GRAY     = "#6b6b6b"
PROMPT_C = "#61afef"
MONO     = ("Consolas", 12)
MONO_SM  = ("Consolas", 11)
MONO_XS  = ("Consolas", 10)


class TerminalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.overrideredirect(True)  # Remove default title bar
        self.geometry("780x520+200+100")
        self.minsize(600, 350)
        self.configure(fg_color=BG)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Custom Title Bar (Linux-style) ──
        title_bar = ctk.CTkFrame(self, fg_color=BG_BAR, corner_radius=0, height=32)
        title_bar.grid(row=0, column=0, sticky="ew")
        title_bar.grid_columnconfigure(1, weight=1)
        title_bar.grid_propagate(False)

        # Traffic light dots
        dots = ctk.CTkFrame(title_bar, fg_color="transparent")
        dots.grid(row=0, column=0, padx=10, pady=8)

        for color, cmd in [("#ff5f57", self.destroy), ("#febc2e", self._minimize), ("#28c840", self._maximize)]:
            dot = ctk.CTkButton(
                dots, text="", width=13, height=13,
                fg_color=color, hover_color=color,
                corner_radius=7, border_width=0,
                command=cmd
            )
            dot.pack(side="left", padx=2)

        title_label = ctk.CTkLabel(
            title_bar, text="smartsort@user: ~",
            font=MONO_SM, text_color=GRAY
        )
        title_label.grid(row=0, column=1, sticky="")

        # Drag window
        title_bar.bind("<Button-1>", self._start_drag)
        title_bar.bind("<B1-Motion>", self._on_drag)
        title_label.bind("<Button-1>", self._start_drag)
        title_label.bind("<B1-Motion>", self._on_drag)

        # ── Terminal Body ──
        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.output = ctk.CTkTextbox(
            body, font=MONO, fg_color=BG, text_color=FG,
            border_width=0, corner_radius=0, wrap="word",
            activate_scrollbars=True,
            scrollbar_button_color=GRAY,
            scrollbar_button_hover_color=FG
        )
        self.output.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 0))
        self.output.configure(state="disabled")

        # ── Prompt Line ──
        prompt_frame = ctk.CTkFrame(body, fg_color=BG, corner_radius=0)
        prompt_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(4, 8))
        prompt_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            prompt_frame, text="smartsort $",
            font=MONO, text_color=PROMPT_C
        ).grid(row=0, column=0, padx=(0, 6))

        self.cmd_input = ctk.CTkEntry(
            prompt_frame, font=MONO, fg_color=BG, text_color=FG,
            border_width=0, corner_radius=0,
            placeholder_text="type a command...",
            placeholder_text_color=GRAY
        )
        self.cmd_input.grid(row=0, column=1, sticky="ew")
        self.cmd_input.bind("<Return>", self._on_enter)
        self.cmd_input.focus()

        # ── Startup ──
        self._print("smartsort v1.0 — file organizer", GREEN)
        self._print("type 'help' for commands\n", GRAY)

        # Resize grip
        self._drag_data = {"x": 0, "y": 0}
        self._is_maximized = False

    # ── Window Controls ──
    def _start_drag(self, event):
        self._drag_data["x"] = event.x_root - self.winfo_x()
        self._drag_data["y"] = event.y_root - self.winfo_y()

    def _on_drag(self, event):
        if self._is_maximized:
            return
        x = event.x_root - self._drag_data["x"]
        y = event.y_root - self._drag_data["y"]
        self.geometry(f"+{x}+{y}")

    def _minimize(self):
        self.overrideredirect(False)
        self.iconify()
        self.after(100, lambda: self.overrideredirect(True))

    def _maximize(self):
        if self._is_maximized:
            self.geometry("780x520+200+100")
            self._is_maximized = False
        else:
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            self._is_maximized = True

    # ── Terminal Output ──
    def _print(self, text, color=FG):
        self.output.configure(state="normal")
        tag = f"t{id(text)}_{os.urandom(4).hex()}"
        start = self.output.index("end-1c")
        self.output.insert(END, text + "\n")
        end = self.output.index("end-1c")
        self.output.tag_add(tag, start, end)
        self.output.tag_config(tag, foreground=color)
        self.output.see(END)
        self.output.configure(state="disabled")

    def _clear(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", END)
        self.output.configure(state="disabled")

    # ── Command Handler ──
    def _on_enter(self, event):
        raw = self.cmd_input.get().strip()
        self.cmd_input.delete(0, END)
        if not raw:
            return

        self._print(f"$ {raw}", PROMPT_C)

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "help":
            self._cmd_help()
        elif cmd == "sort":
            self._cmd_sort(arg, dry_run=False)
        elif cmd == "dry-run":
            self._cmd_sort(arg, dry_run=True)
        elif cmd == "browse":
            self._cmd_browse()
        elif cmd == "ls":
            self._cmd_ls(arg)
        elif cmd == "history":
            self._cmd_history()
        elif cmd == "undo":
            self._cmd_undo(arg)
        elif cmd == "clear":
            self._clear()
        elif cmd == "pwd":
            self._print(os.getcwd(), FG)
        elif cmd in ("exit", "quit"):
            self.destroy()
        else:
            self._print(f"unknown command: {cmd}", RED)

    def _cmd_help(self):
        lines = [
            ("  sort <path>      ", "organize files in a directory"),
            ("  dry-run <path>   ", "simulate without moving files"),
            ("  browse           ", "open folder picker dialog"),
            ("  ls <path>        ", "list files in a directory"),
            ("  history          ", "show recent moves"),
            ("  undo             ", "undo last move"),
            ("  undo all         ", "undo all moves"),
            ("  clear            ", "clear terminal"),
            ("  pwd              ", "print working directory"),
            ("  exit             ", "quit"),
        ]
        self._print("")
        for cmd, desc in lines:
            self._print(f"{cmd} {desc}", FG)
        self._print("")

    def _cmd_browse(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self._print(f"selected: {folder}", CYAN)
            self._print(f"tip: run 'sort {folder}' or 'dry-run {folder}'", GRAY)

    def _cmd_ls(self, path):
        target = path if path else os.getcwd()
        if not os.path.isdir(target):
            self._print(f"not a directory: {target}", RED)
            return
        try:
            entries = sorted(os.listdir(target))
            for e in entries:
                full = os.path.join(target, e)
                if os.path.isdir(full):
                    self._print(f"  {e}/", CYAN)
                else:
                    size = os.path.getsize(full)
                    self._print(f"  {e}  ({self._fsize(size)})", FG)
        except PermissionError:
            self._print("permission denied", RED)

    def _cmd_sort(self, path, dry_run):
        if not path:
            # Open file dialog if no path given
            path = filedialog.askdirectory(title="Select Folder to Organize")
            if not path:
                return

        if not os.path.isdir(path):
            self._print(f"not a directory: {path}", RED)
            return

        config_path = get_config_path()
        if not os.path.exists(config_path):
            self._print(f"config not found: {config_path}", RED)
            return

        mode = "DRY RUN" if dry_run else "SORTING"
        self._print(f"[{mode}] {path}", YELLOW if dry_run else RED)

        threading.Thread(target=self._sort_worker, args=(path, config_path, dry_run), daemon=True).start()

    def _sort_worker(self, folder, config_path, dry_run):
        classifier = FileClassifier(folder, config_path)
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        except Exception as e:
            self.after(0, lambda: self._print(f"error: {e}", RED))
            return

        if not files:
            self.after(0, lambda: self._print("no files found", GRAY))
            return

        moved, skipped, errors = 0, 0, 0

        for item in files:
            result = classifier.process_file(os.path.join(folder, item), dry_run=dry_run)
            status = result.get("status", "error")

            if status == "moved":
                moved += 1
                dest = result.get("destination", "")
                self.after(0, lambda i=item, d=dest: self._print(f"  → {i}  ➜  {os.path.basename(d)}", GREEN))
            elif status == "duplicate":
                skipped += 1
                r = result.get("reason", "")
                self.after(0, lambda i=item, r=r: self._print(f"  ⊘ {i}  ({r})", YELLOW))
            else:
                errors += 1
                r = result.get("reason", "Unknown")
                self.after(0, lambda i=item, r=r: self._print(f"  ✗ {i}  ({r})", RED))

        def done():
            self._print(f"\n  {moved} moved  {skipped} skipped  {errors} errors  ({len(files)} total)", GREEN if errors == 0 else YELLOW)

        self.after(0, done)

    def _cmd_history(self):
        try:
            records = get_history(15)
        except Exception as e:
            self._print(f"error: {e}", RED)
            return
        if not records:
            self._print("no history", GRAY)
            return
        for r in records:
            self._print(f"  #{r[0]}  {os.path.basename(r[1])} → {os.path.basename(r[2])}  ({r[3]})", FG)

    def _cmd_undo(self, arg):
        try:
            records = get_history(None if arg.lower() == "all" else 1) if arg else get_history(1)
        except Exception:
            records = get_history(1)

        if not records:
            self._print("nothing to undo", GRAY)
            return

        for record in records:
            name = os.path.basename(record[1])
            if undo_move(record):
                self._print(f"  ↩ restored: {name}", GREEN)
            else:
                self._print(f"  ✗ failed: {name}", RED)

    @staticmethod
    def _fsize(b):
        for u in ['B','KB','MB','GB']:
            if b < 1024: return f"{b:.0f}{u}"
            b /= 1024
        return f"{b:.0f}TB"


if __name__ == "__main__":
    init_db()
    app = TerminalApp()
    app.mainloop()
