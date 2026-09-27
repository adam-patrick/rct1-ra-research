#!/usr/bin/env python3
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime, timezone
from .rct1_gui import *

MAX_DISPLAY_ROWS = 5_000
CONTINUOUS_MODES = {"changed", "unchanged", "increased", "decreased", "increased_by", "decreased_by"}

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("RCT1 Read-Only Memory Research"); self.geometry("1180x760")
        self.info = None; self.provider = None; self.engine = None; self.watches = []; self.watch_keys = set()
        self.scanning = False
        self.continuous = tk.BooleanVar(value=False)
        self.continuous_job = None
        self.sort_column = None
        self.sort_reverse = False
        self._build(); self.after(1000, self.refresh_status)
    def _build(self):
        status = ttk.LabelFrame(self, text="Process / Game Status"); status.pack(fill="x", padx=8, pady=8)
        self.status_text = tk.StringVar(value="Disconnected")
        ttk.Label(status, textvariable=self.status_text, justify="left").pack(side="left", padx=8, pady=5)
        ttk.Button(status, text="Reconnect", command=self.refresh_status).pack(side="right", padx=8)
        state = ttk.LabelFrame(self, text="Validated RCT State (read-only)"); state.pack(fill="x", padx=8, pady=4)
        self.state_text = tk.StringVar(value="Unavailable")
        ttk.Label(state, textvariable=self.state_text, justify="left").pack(side="left", padx=8, pady=5)
        controls = ttk.LabelFrame(self, text="Memory Search"); controls.pack(fill="x", padx=8, pady=4)
        self.mode = ttk.Combobox(controls, values=["exact", "unknown", "changed", "unchanged", "increased", "decreased", "increased_by", "decreased_by"], state="readonly", width=16); self.mode.set("exact"); self.mode.pack(side="left", padx=4, pady=5)
        self.value = ttk.Entry(controls, width=14); self.value.insert(0, "0"); self.value.pack(side="left", padx=4)
        self.typevar = tk.StringVar(value="u16"); ttk.Combobox(controls, textvariable=self.typevar, values=list(TYPES), state="readonly", width=7).pack(side="left", padx=4)
        ttk.Label(controls, text="Range +").pack(side="left", padx=(8, 2)); self.range_start = ttk.Entry(controls, width=9); self.range_start.pack(side="left")
        ttk.Label(controls, text="to").pack(side="left", padx=2); self.range_end = ttk.Entry(controls, width=9); self.range_end.pack(side="left")
        self.scan_button = ttk.Button(controls, text="Run scan/filter", command=self.run_scan); self.scan_button.pack(side="left", padx=4)
        ttk.Button(controls, text="Cancel", command=self.cancel_scan).pack(side="left", padx=4)
        ttk.Checkbutton(controls, text="Continuous filter (1s)", variable=self.continuous).pack(side="left", padx=4)
        self.progress = ttk.Progressbar(controls, mode="determinate"); self.progress.pack(side="left", fill="x", expand=True, padx=8)
        self.count = tk.StringVar(value="Candidates: 0"); ttk.Label(controls, textvariable=self.count).pack(side="right", padx=5)
        frame = ttk.Frame(self); frame.pack(fill="both", expand=True, padx=8, pady=4)
        columns = ("address", "relative", "type", "current", "previous", "delta", "history", "label", "status")
        self.table = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
        for col in columns:
            self.table.heading(col, text=col.replace("_", " ").title(), command=lambda column=col: self.sort_candidates(column))
            self.table.column(col, width=120)
        self.table.pack(side="left", fill="both", expand=True); self.table.bind("<<TreeviewSelect>>", self.inspect)
        self.table.tag_configure("watched", background="#fff1a8")
        scroll = ttk.Scrollbar(frame, command=self.table.yview); scroll.pack(side="right", fill="y"); self.table.configure(yscrollcommand=scroll.set)
        bottom = ttk.Frame(self); bottom.pack(fill="x", padx=8, pady=5)
        ttk.Button(bottom, text="Add bookmark", command=self.bookmark).pack(side="left", padx=3)
        ttk.Button(bottom, text="Watch selected", command=self.watch_selected).pack(side="left", padx=3)
        ttk.Button(bottom, text="Refresh watches", command=self.refresh_watches).pack(side="left", padx=3)
        ttk.Button(bottom, text="Save session", command=self.save_session).pack(side="left", padx=3)
        ttk.Button(bottom, text="Load session", command=self.load_session).pack(side="left", padx=3)
        self.inspector = tk.StringVar(value="Select a candidate for read-only neighborhood inspection."); ttk.Label(bottom, textvariable=self.inspector).pack(side="left", padx=15)
    def refresh_status(self):
        old = self.info.pid if self.info else None
        self.info = find_process(); self.provider = MemoryProvider(self.info) if self.info else None
        if not self.info:
            self.status_text.set("RCT1: DISCONNECTED\nMemory Access: unavailable\nScan: idle"); self.state_text.set("Unavailable"); self.after(1500, self.refresh_status); return
        changed = old is not None and old != self.info.pid
        self.status_text.set(f"RCT1: CONNECTED\nPID: {self.info.pid}\nPath: {self.info.path}\nModule Base: 0x{self.info.base:08x}\nBuild: {(self.info.build_hash or 'unavailable')}\nBuild Status: {self.info.build_status}\nMemory Access: Read Only\nScan: {'process changed; reconnecting' if changed else 'ready'}")
        if self.info.build_status == "Supported":
            values = read_state(self.provider); self.state_text.set(f"Cash: {format_cash(values['cash']) if values['cash'] is not None else 'unavailable'}\nGuests: {values['guest_count']}\nPark Rating: {values['park_rating']}\nSnapshot: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
        else: self.state_text.set("Unsupported/unknown build; validated fields hidden")
        self.after(1500, self.refresh_status)
    def run_scan(self):
        if self.scanning: return
        if not self.provider or self.info.build_status != "Supported": return messagebox.showwarning("Unavailable", "Connect to the supported RCT.EXE build first.")
        mode = self.mode.get()
        if self.continuous.get() and mode not in CONTINUOUS_MODES:
            self.continuous.set(False)
            return messagebox.showwarning("Continuous filter", "Continuous mode is available for refinement filters only.")
        if self.engine is None or self.engine.provider.info.pid != self.info.pid: self.engine = SearchEngine(self.provider, lambda done,total: self.after(0, lambda: self.progress.configure(value=(done / total * 100) if total else 0)))
        value = int(self.value.get(), 0) if mode not in ("unknown",) else None
        scan_start = int(self.range_start.get(), 0) if self.range_start.get().strip() else None
        scan_end = int(self.range_end.get(), 0) if self.range_end.get().strip() else None
        if scan_start is not None and scan_end is not None and scan_end <= scan_start:
            return messagebox.showwarning("Scan range", "Range end must be greater than range start.")
        self.progress.configure(value=0); self.engine.cancel.clear(); self.scanning = True; self.scan_button.configure(state="disabled")
        threading.Thread(target=self._scan_thread, args=(mode, value, scan_start, scan_end), daemon=True).start()
    def _scan_thread(self, mode, value, scan_start, scan_end):
        try:
            self.engine.scan(mode, value, [self.typevar.get()], value or 0 if mode.endswith("_by") else 0, scan_start, scan_end)
            self.after(0, lambda: self.populate(mode))
        except Exception as error:
            self.after(0, lambda: self.scan_failed(error))
    def cancel_scan(self):
        self.continuous.set(False)
        if self.continuous_job is not None:
            self.after_cancel(self.continuous_job); self.continuous_job = None
        if self.engine: self.engine.cancel.set()
    def scan_failed(self, error):
        self.scanning = False; self.continuous.set(False); self.scan_button.configure(state="normal")
        messagebox.showerror("Scan failed", f"{type(error).__name__}: {error}")
    def populate(self, completed_mode=None):
        self.scanning = False; self.scan_button.configure(state="normal")
        self.table.delete(*self.table.get_children())
        if self.engine and self.engine.baseline:
            self.count.set(self.engine.scan_message or "Unknown baseline captured; perform a transition, then filter")
        else:
            count = len(self.engine.candidates) if self.engine else 0
            message = f" ({self.engine.scan_message})" if self.engine and self.engine.scan_message else ""
            self.count.set(f"Candidates: {count:,}{message}")
        candidates = self.engine.candidates if self.engine else []
        indexed = list(enumerate(candidates))
        if self.sort_column:
            indexed.sort(key=lambda item: self.sort_key(item[1], self.sort_column), reverse=self.sort_reverse)
        for index, c in indexed[:MAX_DISPLAY_ROWS]:
            history = ",".join(str(value) for value in c.history[-8:])
            tags = ("watched",) if (c.relative, c.type_name) in self.watch_keys else ()
            self.table.insert("", "end", iid=str(index), values=(f"0x{c.address:08x}", f"+0x{c.relative:x}", c.type_name, c.current, c.previous, c.delta, history, c.label, c.status), tags=tags)
        if len(candidates) > MAX_DISPLAY_ROWS:
            self.count.set(f"Candidates: {len(candidates):,} (showing first {MAX_DISPLAY_ROWS:,}; narrow the scan before inspecting)")
        if (self.continuous.get() and completed_mode in CONTINUOUS_MODES and
                self.engine and not self.engine.cancel.is_set() and self.info and
                self.engine.provider.info.pid == self.info.pid):
            self.continuous_job = self.after(1000, self.run_scan)
    def sort_key(self, candidate, column):
        if column == "address": return candidate.address
        if column == "relative": return candidate.relative
        if column == "type": return candidate.type_name
        if column == "current": return candidate.current
        if column == "previous": return candidate.previous
        if column == "delta": return candidate.delta
        if column == "history": return tuple(candidate.history)
        if column == "label": return candidate.label.lower()
        return candidate.status.lower()
    def sort_candidates(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column, self.sort_reverse = column, False
        self.populate()
    def selected(self):
        return [self.engine.candidates[int(x)] for x in self.table.selection()]
    def inspect(self, _event=None):
        selected = self.selected()
        if selected and self.provider:
            c = selected[0]
            try: data = self.provider.read(max(0, c.address - 16), 32); self.inspector.set(f"0x{c.address:08x} (+0x{c.relative:x})  {data.hex(' ')}  [read-only neighborhood ±16 bytes]")
            except OSError: self.inspector.set("Selected address is unavailable (process may have restarted).")
    def bookmark(self):
        if not self.info or self.info.build_status != "Supported" or not self.selected(): return
        c = self.selected()[0]
        store = MetadataStore(); data = store.load(); locations = data.get("builds", {}).get(self.info.build_hash, {}).get("locations", [])
        bookmark_id = f"candidate_{c.relative:x}"
        existing = next((item for item in locations if item.get("id") == bookmark_id), {})
        details = self.edit_bookmark(existing, c)
        if details is None: return
        today = datetime.now(timezone.utc).date().isoformat()
        loc = {"id": bookmark_id, "label": details["label"], "module": "RCT.EXE", "offset": f"0x{c.relative:x}", "type": c.type_name,
               "status": details["status"], "confidence": details["confidence"], "build_hash": self.info.build_hash,
               "notes": details["notes"], "date_discovered": existing.get("date_discovered", today),
               "date_last_validated": today if details["status"] == "validated" else existing.get("date_last_validated")}
        store.save_location(self.info.build_hash, loc)
        messagebox.showinfo("Bookmark saved", f"Saved {details['label']} to {METADATA_PATH}")
    def edit_bookmark(self, existing, candidate):
        dialog = tk.Toplevel(self); dialog.title("Add / Edit Bookmark"); dialog.transient(self); dialog.grab_set()
        fields = {"label": existing.get("label", f"Candidate 0x{candidate.relative:x}"),
                  "status": existing.get("status", "candidate"), "confidence": existing.get("confidence", "low"),
                  "notes": existing.get("notes", "")}
        variables = {name: tk.StringVar(value=value) for name, value in fields.items()}
        metadata = [("Address", f"0x{candidate.address:08x}"), ("Module Relative", f"+0x{candidate.relative:x}"), ("Type", candidate.type_name), ("Build", self.info.build_hash or "unavailable")]
        for row, (name, value) in enumerate(metadata):
            ttk.Label(dialog, text=name).grid(row=row, column=0, padx=10, pady=3, sticky="w")
            ttk.Label(dialog, text=value).grid(row=row, column=1, padx=10, pady=3, sticky="w")
        ttk.Label(dialog, text="Label").grid(row=4, column=0, padx=10, pady=4, sticky="w")
        ttk.Entry(dialog, textvariable=variables["label"], width=42).grid(row=4, column=1, padx=10, pady=4)
        ttk.Label(dialog, text="Status").grid(row=5, column=0, padx=10, pady=4, sticky="w")
        ttk.Combobox(dialog, textvariable=variables["status"], values=["candidate", "observed", "validated", "failed", "deprecated"], state="readonly", width=39).grid(row=5, column=1, padx=10, pady=4)
        ttk.Label(dialog, text="Confidence").grid(row=6, column=0, padx=10, pady=4, sticky="w")
        ttk.Combobox(dialog, textvariable=variables["confidence"], values=["low", "medium", "high"], state="readonly", width=39).grid(row=6, column=1, padx=10, pady=4)
        ttk.Label(dialog, text="Notes").grid(row=7, column=0, padx=10, pady=4, sticky="nw")
        ttk.Entry(dialog, textvariable=variables["notes"], width=42).grid(row=7, column=1, padx=10, pady=4)
        result = []
        def save():
            label = variables["label"].get().strip()
            if not label: return messagebox.showwarning("Bookmark", "Label is required.", parent=dialog)
            result.append({name: variables[name].get().strip() for name in variables}); dialog.destroy()
        buttons = ttk.Frame(dialog); buttons.grid(row=8, column=0, columnspan=2, pady=10)
        ttk.Button(buttons, text="Save", command=save).pack(side="left", padx=5)
        ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)
        self.wait_window(dialog)
        return result[0] if result else None
    def watch_selected(self):
        for c in self.selected():
            self.watch_keys.add((c.relative, c.type_name))
            if c not in self.watches: self.watches.append(c)
        self.populate()
    def refresh_watches(self):
        if not self.provider: return
        refreshed = []
        for key in self.watch_keys:
            candidates = [c for c in (self.engine.candidates if self.engine else []) if (c.relative, c.type_name) == key]
            if not candidates: continue
            c = candidates[0]
            try:
                c.previous, c.current = c.current, interpret(self.provider.read(c.address, TYPES[c.type_name][0]), c.type_name)
                refreshed.append(c)
            except OSError: pass
        self.watches = refreshed
        self.populate()
    def save_session(self):
        if not self.engine: return
        path = filedialog.asksaveasfilename(initialdir=str(ROOT / "gui" / "sessions"), defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            self.engine.save_session(Path(path)); messagebox.showinfo("Session saved", path)
    def load_session(self):
        if not self.provider or self.info.build_status != "Supported": return
        path = filedialog.askopenfilename(initialdir=str(ROOT / "gui" / "sessions"), filetypes=[("JSON", "*.json")])
        if path:
            try:
                self.engine = SearchEngine(self.provider); self.engine.load_session(Path(path)); self.populate()
            except (OSError, ValueError, json.JSONDecodeError) as error:
                messagebox.showerror("Session load failed", str(error))

def main(): App().mainloop()
