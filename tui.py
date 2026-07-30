import os
import sys
import threading
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, END

from smartsort.classifier import FileClassifier
from smartsort.history import get_history, undo_move, init_db
from smartsort.cleaner import remove_empty_folders
from smartsort.analyzer import analyze_directory, format_size as fmt_size

def get_config_path() -> str:
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'config', 'rules.yaml')

# ── Modern React/Electron App Color Palette ──
BG           = "#0b0f17"  # Deep Obsidian Black
SIDEBAR_BG   = "#0f172a"  # Slate Navy Sidebar
CARD_BG      = "#1e293b"  # Sleek Dark Card Surface
CARD_BORDER  = "#334155"  # Subtle Border
INPUT_BG     = "#0f172a"

TEXT_MAIN    = "#f8fafc"  # Bright Off-White
TEXT_MUTED   = "#94a3b8"  # Muted Slate Gray

PRIMARY      = "#10b981"  # Emerald Green
PRIMARY_HOVER= "#059669"
BLUE         = "#38bdf8"  # Electric Blue
BLUE_HOVER   = "#0284c7"
AMBER        = "#f59e0b"  # Warm Amber
RED          = "#f43f5e"  # Rose Red
PURPLE       = "#a855f7"  # Electric Purple

FONT_BODY    = ("Segoe UI", 12)
FONT_BOLD    = ("Segoe UI", 12, "bold")
FONT_SM      = ("Segoe UI", 11)
FONT_HEADING = ("Segoe UI", 15, "bold")
FONT_TITLE   = ("Segoe UI", 20, "bold")
FONT_MONO    = ("Consolas", 11)


class SmartSortApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Window Settings ──
        self.title("SmartSort — Desktop File Organizer")
        self.geometry("960x640")
        self.minsize(820, 520)
        self.configure(fg_color=BG)
        ctk.set_appearance_mode("dark")

        # Grid layout: Sidebar (col 0), Main Content (col 1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──
        sidebar = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, width=220, corner_radius=0, border_width=1, border_color=CARD_BORDER)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(4, weight=1)

        # Brand Title
        brand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand_frame.pack(padx=16, pady=24, fill="x")

        ctk.CTkLabel(
            brand_frame, text="⚡ SmartSort",
            font=FONT_TITLE, text_color=TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_frame, text="v1.2.0 Desktop Engine",
            font=FONT_SM, text_color=PRIMARY
        ).pack(anchor="w", pady=(2, 0))

        # Navigation Buttons
        self.btn_nav_dashboard = ctk.CTkButton(
            sidebar, text="  ❖  Dashboard", font=FONT_BOLD, height=38,
            fg_color=CARD_BG, text_color=PRIMARY, hover_color=CARD_BORDER,
            anchor="w", corner_radius=8, command=lambda: self.switch_tab("dashboard")
        )
        self.btn_nav_dashboard.pack(padx=12, pady=4, fill="x")

        self.btn_nav_analyzer = ctk.CTkButton(
            sidebar, text="  📊  Storage Analyzer", font=FONT_BOLD, height=38,
            fg_color="transparent", text_color=TEXT_MUTED, hover_color=CARD_BG,
            anchor="w", corner_radius=8, command=lambda: self.switch_tab("analyzer")
        )
        self.btn_nav_analyzer.pack(padx=12, pady=4, fill="x")

        self.btn_nav_history = ctk.CTkButton(
            sidebar, text="  🕒  Move History", font=FONT_BOLD, height=38,
            fg_color="transparent", text_color=TEXT_MUTED, hover_color=CARD_BG,
            anchor="w", corner_radius=8, command=lambda: self.switch_tab("history")
        )
        self.btn_nav_history.pack(padx=12, pady=4, fill="x")

        # Sidebar Footer Status
        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.pack(side="bottom", padx=16, pady=16)

        ctk.CTkLabel(
            footer, text="● System Online",
            font=FONT_SM, text_color=PRIMARY
        ).pack(anchor="w")

        # ── Main Content Container ──
        self.main_container = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(2, weight=1)

        # ── Top Folder Selector Card ──
        header_card = ctk.CTkFrame(self.main_container, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        header_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header_card.grid_columnconfigure(0, weight=1)

        self.folder_var = ctk.StringVar(value="")
        self.folder_entry = ctk.CTkEntry(
            header_card, textvariable=self.folder_var,
            placeholder_text="Select target folder to organize...",
            font=FONT_BODY, height=40,
            fg_color=INPUT_BG, border_color=CARD_BORDER, border_width=1,
            text_color=BLUE, placeholder_text_color=TEXT_MUTED,
            corner_radius=8
        )
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=16, pady=14)

        ctk.CTkButton(
            header_card, text="📁 Browse Folder", width=140, height=40,
            font=FONT_BOLD, fg_color=BLUE, hover_color=BLUE_HOVER,
            text_color="#ffffff", corner_radius=8,
            command=self.browse_folder
        ).grid(row=0, column=1, padx=(0, 16), pady=14)

        # ── Dashboard Tab View ──
        self.tab_dashboard = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.tab_dashboard.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.tab_dashboard.grid_columnconfigure(0, weight=1)
        self.tab_dashboard.grid_rowconfigure(2, weight=1)

        # Stats Summary Cards Row
        stats_row = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        stats_row.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        stats_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")

        self.card_files = self._create_stat_card(stats_row, 0, "Total Files", "0", "📁", BLUE)
        self.card_size  = self._create_stat_card(stats_row, 1, "Storage Used", "0 MB", "💾", PRIMARY)
        self.card_cats  = self._create_stat_card(stats_row, 2, "Categories", "0", "🏷️", PURPLE)
        self.card_dups  = self._create_stat_card(stats_row, 3, "Duplicates", "0", "⚠️", AMBER)

        # Action Buttons Toolbar
        action_card = ctk.CTkFrame(self.tab_dashboard, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        action_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        action_inner = ctk.CTkFrame(action_card, fg_color="transparent")
        action_inner.pack(padx=16, pady=12, fill="x")

        ctk.CTkButton(
            action_inner, text="⚡ Organize Now", width=140, height=38,
            font=FONT_BOLD, fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            text_color="#ffffff", corner_radius=8,
            command=lambda: self.run_sort(False)
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_inner, text="🔍 Dry Run", width=110, height=38,
            font=FONT_BOLD, fg_color=INPUT_BG, hover_color=CARD_BORDER,
            text_color=BLUE, border_width=1, border_color=CARD_BORDER, corner_radius=8,
            command=lambda: self.run_sort(True)
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_inner, text="📊 Scan Storage", width=120, height=38,
            font=FONT_BOLD, fg_color=INPUT_BG, hover_color=CARD_BORDER,
            text_color=BLUE, border_width=1, border_color=CARD_BORDER, corner_radius=8,
            command=self.cmd_scan
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_inner, text="🧹 Clean Empty", width=120, height=38,
            font=FONT_BOLD, fg_color=INPUT_BG, hover_color=CARD_BORDER,
            text_color=AMBER, border_width=1, border_color=CARD_BORDER, corner_radius=8,
            command=self.cmd_clean_empty
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_inner, text="↩ Undo Last", width=110, height=38,
            font=FONT_BOLD, fg_color=INPUT_BG, hover_color=CARD_BORDER,
            text_color=PURPLE, border_width=1, border_color=CARD_BORDER, corner_radius=8,
            command=self.undo_last
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_inner, text="🗑 Clear Log", width=100, height=38,
            font=FONT_BODY, fg_color="transparent", hover_color=INPUT_BG,
            text_color=TEXT_MUTED, corner_radius=8,
            command=self.clear_terminal
        ).pack(side="right", padx=4)

        # Activity Log Card Window
        log_card = ctk.CTkFrame(self.tab_dashboard, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        log_card.grid(row=2, column=0, sticky="nsew")
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(1, weight=1)

        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            log_header, text="Activity Log & Console Stream",
            font=FONT_HEADING, text_color=TEXT_MAIN
        ).pack(side="left")

        self.terminal = ctk.CTkTextbox(
            log_card, font=FONT_MONO,
            fg_color=INPUT_BG, text_color=TEXT_MAIN,
            border_width=1, border_color=CARD_BORDER, corner_radius=8, wrap="word",
            activate_scrollbars=True
        )
        self.terminal.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.terminal.configure(state="disabled")

        # Initial Welcome Log
        self._print("SmartSort Engine Ready. Select a folder and click [ Organize Now ] to begin.", PRIMARY)

    def _create_stat_card(self, parent, col, title, value, icon, color):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.grid(row=0, column=col, sticky="ew", padx=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=16, pady=14, fill="x")

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(top, text=title.upper(), font=FONT_SM, text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(top, text=icon, font=FONT_HEADING).pack(side="right")

        val_label = ctk.CTkLabel(inner, text=value, font=FONT_TITLE, text_color=color)
        val_label.pack(anchor="w", pady=(6, 0))
        return val_label

    def switch_tab(self, tab_name):
        # Update Nav styles
        self.btn_nav_dashboard.configure(fg_color=CARD_BG if tab_name == "dashboard" else "transparent", text_color=PRIMARY if tab_name == "dashboard" else TEXT_MUTED)
        self.btn_nav_analyzer.configure(fg_color=CARD_BG if tab_name == "analyzer" else "transparent", text_color=BLUE if tab_name == "analyzer" else TEXT_MUTED)
        self.btn_nav_history.configure(fg_color=CARD_BG if tab_name == "history" else "transparent", text_color=PURPLE if tab_name == "history" else TEXT_MUTED)

        if tab_name == "dashboard":
            self.tab_dashboard.lift()
        elif tab_name == "analyzer":
            self.cmd_scan()
        elif tab_name == "history":
            self.show_history()

    # ── Output Helpers ──
    def _print(self, text: str, color: str = TEXT_MAIN):
        self.terminal.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        tag = f"t{id(text)}_{os.urandom(4).hex()}"
        start = self.terminal.index("end-1c")
        self.terminal.insert(END, f"[{timestamp}] {text}\n")
        end = self.terminal.index("end-1c")
        self.terminal.tag_add(tag, start, end)
        self.terminal.tag_config(tag, foreground=color)
        self.terminal.see(END)
        self.terminal.configure(state="disabled")

    def clear_terminal(self):
        self.terminal.configure(state="normal")
        self.terminal.delete("1.0", END)
        self.terminal.configure(state="disabled")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        if folder:
            self.folder_var.set(folder)
            self._print(f"Target directory set: {folder}", BLUE)
            self.cmd_scan()

    def cmd_scan(self):
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            return

        config_path = get_config_path()
        summary = analyze_directory(folder, config_path)
        
        self.card_files.configure(text=str(summary['total_files']))
        self.card_size.configure(text=fmt_size(summary['total_size']))
        self.card_cats.configure(text=str(len(summary['categories'])))

        self._print(f"Storage scan complete for {folder}: {summary['total_files']} files ({fmt_size(summary['total_size'])}).", PRIMARY)

    def cmd_clean_empty(self):
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            self._print("Please select a target folder first.", RED)
            return

        removed = remove_empty_folders(folder, dry_run=False)
        if not removed:
            self._print("No empty subfolders found.", AMBER)
        else:
            self._print(f"Cleaned {len(removed)} empty subfolder(s).", PRIMARY)

    def run_sort(self, dry_run: bool):
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            folder = filedialog.askdirectory(title="Select Folder to Organize")
            if not folder:
                self._print("Please select a valid folder.", RED)
                return
            self.folder_var.set(folder)

        config_path = get_config_path()
        mode = "DRY RUN SIMULATION" if dry_run else "EXECUTING SORT"
        self._print(f"Starting [{mode}] on: {folder}", AMBER if dry_run else PRIMARY)

        threading.Thread(
            target=self._sort_worker, args=(folder, config_path, dry_run),
            daemon=True
        ).start()

    def _sort_worker(self, folder, config_path, dry_run):
        classifier = FileClassifier(folder, config_path)
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        except Exception as e:
            self.after(0, lambda: self._print(f"Error accessing folder: {e}", RED))
            return

        if not files:
            self.after(0, lambda: self._print("No files found to organize.", AMBER))
            return

        moved, duplicates, errors = 0, 0, 0

        for item in files:
            result = classifier.process_file(os.path.join(folder, item), dry_run=dry_run)
            status = result.get("status", "error")

            if status == "moved":
                moved += 1
                dest = os.path.basename(result.get("destination", ""))
                self.after(0, lambda i=item, d=dest: self._print(f"MOVED: {i}  ──>  {d}", PRIMARY))
            elif status == "duplicate":
                duplicates += 1
                dest = os.path.join("Duplicates", os.path.basename(result.get("destination", "")))
                self.after(0, lambda i=item, d=dest: self._print(f"DUPLICATE: {i}  ──>  {d}", AMBER))
            else:
                errors += 1
                r = result.get("reason", "Unknown")
                self.after(0, lambda i=item, r=r: self._print(f"ERROR: {i} ({r})", RED))

        def finish():
            self.card_dups.configure(text=str(duplicates))
            self._print(f"Complete! Moved: {moved} | Duplicates: {duplicates} | Errors: {errors}", PRIMARY if errors == 0 else AMBER)
            self.cmd_scan()

        self.after(0, finish)

    def show_history(self):
        try:
            records = get_history(15)
        except Exception as e:
            self._print(f"History error: {e}", RED)
            return

        if not records:
            self._print("No move history recorded.", AMBER)
            return

        self._print("=== RECENT MOVE HISTORY ===", PURPLE)
        for r in records:
            self._print(f"#{r[0]} | {os.path.basename(r[1])} ──> {os.path.basename(r[2])} [{r[3]}]", TEXT_MAIN)

    def undo_last(self):
        try:
            records = get_history(1)
        except Exception as e:
            self._print(f"Undo error: {e}", RED)
            return

        if not records:
            self._print("Nothing to undo.", AMBER)
            return

        for record in records:
            name = os.path.basename(record[1])
            if undo_move(record):
                self._print(f"Restored: {name}", PRIMARY)
            else:
                self._print(f"Could not restore: {name}", RED)


if __name__ == "__main__":
    init_db()
    app = SmartSortApp()
    app.mainloop()
