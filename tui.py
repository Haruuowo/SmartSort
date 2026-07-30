import os
import sys
import threading
import customtkinter as ctk
from tkinter import filedialog, ttk

from smartsort.classifier import FileClassifier
from smartsort.history import get_history, undo_move, init_db

def get_config_path() -> str:
    """Resolve config path for both dev and bundled exe."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'config', 'rules.yaml')


class SmartSortApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Window Config ──
        self.title("SmartSort — File Organizer")
        self.geometry("960x640")
        self.minsize(800, 500)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # ── Main Layout ──
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="SmartSort",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color="#7f5af0"
        ).grid(row=0, column=0, padx=20, pady=(15, 2), sticky="w")

        ctk.CTkLabel(
            header, text="Organize your files intelligently",
            font=ctk.CTkFont(size=13),
            text_color="#94a1b2"
        ).grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        # ── Controls Bar ──
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", padx=20, pady=(15, 5))
        controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(controls, text="Target Folder:", font=ctk.CTkFont(size=13)).grid(
            row=0, column=0, padx=(0, 10)
        )

        self.folder_var = ctk.StringVar(value="")
        self.folder_entry = ctk.CTkEntry(
            controls, textvariable=self.folder_var,
            placeholder_text="Select a folder to organize...",
            height=36, font=ctk.CTkFont(size=13)
        )
        self.folder_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        ctk.CTkButton(
            controls, text="Browse", width=90, height=36,
            fg_color="#7f5af0", hover_color="#6b4acf",
            command=self.browse_folder
        ).grid(row=0, column=2, padx=(0, 10))

        # ── Action Buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="e", padx=20, pady=(55, 0))

        self.dry_run_btn = ctk.CTkButton(
            btn_frame, text="⚡ Dry Run", width=120, height=36,
            fg_color="#2cb67d", hover_color="#239d6a",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.run_sort(dry_run=True)
        )
        self.dry_run_btn.pack(side="left", padx=5)

        self.sort_btn = ctk.CTkButton(
            btn_frame, text="🚀 Organize", width=120, height=36,
            fg_color="#e53170", hover_color="#c42a60",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.run_sort(dry_run=False)
        )
        self.sort_btn.pack(side="left", padx=5)

        self.undo_btn = ctk.CTkButton(
            btn_frame, text="↩ Undo Last", width=120, height=36,
            fg_color="#3a3a5c", hover_color="#4a4a6c",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.undo_last
        )
        self.undo_btn.pack(side="left", padx=5)

        # ── Stats Cards ──
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=2, column=0, sticky="new", padx=20, pady=(10, 0))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_labels = {}
        stat_configs = [
            ("Total", "#94a1b2", "total"),
            ("Moved", "#2cb67d", "moved"),
            ("Skipped", "#e5a00d", "skipped"),
            ("Errors", "#e53170", "errors"),
        ]
        for i, (label, color, key) in enumerate(stat_configs):
            card = ctk.CTkFrame(stats_frame, fg_color="#1a1a2e", corner_radius=12, height=80)
            card.grid(row=0, column=i, padx=6, sticky="ew")
            card.grid_propagate(False)
            card.grid_columnconfigure(0, weight=1)

            val_label = ctk.CTkLabel(
                card, text="0",
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color=color
            )
            val_label.grid(row=0, column=0, pady=(12, 0))

            ctk.CTkLabel(
                card, text=label,
                font=ctk.CTkFont(size=11),
                text_color="#72757e"
            ).grid(row=1, column=0, pady=(0, 8))

            self.stat_labels[key] = val_label

        # ── Results Table ──
        table_frame = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=12)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(10, 20))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            table_frame, text="Results",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#fffffe"
        ).grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        # Style the treeview to match dark theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Treeview",
            background="#16162a",
            foreground="#fffffe",
            fieldbackground="#16162a",
            borderwidth=0,
            font=("Segoe UI", 11),
            rowheight=28
        )
        style.configure("Dark.Treeview.Heading",
            background="#242442",
            foreground="#94a1b2",
            borderwidth=0,
            font=("Segoe UI", 11, "bold")
        )
        style.map("Dark.Treeview",
            background=[("selected", "#7f5af0")],
            foreground=[("selected", "#ffffff")]
        )
        style.map("Dark.Treeview.Heading",
            background=[("active", "#2e2e4e")]
        )

        self.tree = ttk.Treeview(
            table_frame, columns=("file", "status", "detail"),
            show="headings", style="Dark.Treeview"
        )
        self.tree.heading("file", text="File")
        self.tree.heading("status", text="Status")
        self.tree.heading("detail", text="Destination / Reason")
        self.tree.column("file", width=220)
        self.tree.column("status", width=100)
        self.tree.column("detail", width=400)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        scrollbar = ctk.CTkScrollbar(table_frame, command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 5), pady=(0, 10))
        self.tree.configure(yscrollcommand=scrollbar.set)

        # ── Status Bar ──
        self.status_var = ctk.StringVar(value="Ready. Select a folder to get started.")
        ctk.CTkLabel(
            self, textvariable=self.status_var,
            font=ctk.CTkFont(size=11),
            text_color="#72757e",
            anchor="w"
        ).grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))

    # ── Actions ──
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        if folder:
            self.folder_var.set(folder)

    def run_sort(self, dry_run: bool):
        folder = self.folder_var.get()
        if not folder or not os.path.isdir(folder):
            self.status_var.set("⚠️  Please select a valid folder first.")
            return

        config_path = get_config_path()
        if not os.path.exists(config_path):
            self.status_var.set(f"⚠️  Config not found: {config_path}")
            return

        mode = "Simulating" if dry_run else "Organizing"
        self.status_var.set(f"⏳ {mode} files in {folder}...")
        self.sort_btn.configure(state="disabled")
        self.dry_run_btn.configure(state="disabled")

        # Run in a thread to keep the UI responsive
        threading.Thread(
            target=self._sort_worker, args=(folder, config_path, dry_run),
            daemon=True
        ).start()

    def _sort_worker(self, folder, config_path, dry_run):
        classifier = FileClassifier(folder, config_path)

        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"❌ Error: {e}"))
            self.after(0, self._enable_buttons)
            return

        # Clear previous results
        self.after(0, lambda: self.tree.delete(*self.tree.get_children()))

        moved, skipped, errors = 0, 0, 0

        for item in files:
            item_path = os.path.join(folder, item)
            result = classifier.process_file(item_path, dry_run=dry_run)
            status = result.get("status", "error")

            if status == "moved":
                moved += 1
                detail = result.get("destination", "")
                tag = "moved"
            elif status == "duplicate":
                skipped += 1
                detail = result.get("reason", "")
                tag = "skipped"
            else:
                errors += 1
                detail = result.get("reason", "Unknown")
                tag = "error"

            self.after(0, lambda i=item, s=status.capitalize(), d=detail, t=tag:
                self._add_row(i, s, d, t))

        total = len(files)
        self.after(0, lambda: self._update_stats(total, moved, skipped, errors))
        mode = "Simulation" if dry_run else "Organization"
        self.after(0, lambda: self.status_var.set(
            f"✅ {mode} complete — {moved} moved, {skipped} skipped, {errors} errors out of {total} files."
        ))
        self.after(0, self._enable_buttons)

    def _add_row(self, file, status, detail, tag):
        self.tree.insert("", "end", values=(file, status, detail), tags=(tag,))
        self.tree.tag_configure("moved", foreground="#2cb67d")
        self.tree.tag_configure("skipped", foreground="#e5a00d")
        self.tree.tag_configure("error", foreground="#e53170")

    def _update_stats(self, total, moved, skipped, errors):
        self.stat_labels["total"].configure(text=str(total))
        self.stat_labels["moved"].configure(text=str(moved))
        self.stat_labels["skipped"].configure(text=str(skipped))
        self.stat_labels["errors"].configure(text=str(errors))

    def _enable_buttons(self):
        self.sort_btn.configure(state="normal")
        self.dry_run_btn.configure(state="normal")

    def undo_last(self):
        try:
            records = get_history(1)
        except Exception as e:
            self.status_var.set(f"❌ Undo error: {e}")
            return

        if not records:
            self.status_var.set("ℹ️ Nothing to undo.")
            return

        record = records[0]
        name = os.path.basename(record[1])
        success = undo_move(record)
        if success:
            self.status_var.set(f"✅ Restored: {name}")
        else:
            self.status_var.set(f"❌ Failed to restore: {name}")


if __name__ == "__main__":
    init_db()
    app = SmartSortApp()
    app.mainloop()
