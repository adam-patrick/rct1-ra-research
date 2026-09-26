#!/usr/bin/env python3
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime, timezone
from .rct1_gui import *

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("RCT1 Read-Only Memory Research"); self.geometry("1180x760")
        self.info = None; self.provider = None; self.engine = None; self.watches = []
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
        ttk.Button(controls, text="Run scan/filter", command=self.run_scan).pack(side="left", padx=4)
        ttk.Button(controls, text="Cancel", command=self.cancel_scan).pack(side="left", padx=4)
        self.progress = ttk.Progressbar(controls, mode="determinate"); self.progress.pack(side="left", fill="x", expand=True, padx=8)
        self.count = tk.StringVar(value="Candidates: 0"); ttk.Label(controls, textvariable=self.count).pack(side="right", padx=5)
        frame = ttk.Frame(self); frame.pack(fill="both", expand=True, padx=8, pady=4)
        columns = ("address", "relative", "type", "current", "previous", "delta", "label", "status")
        self.table = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
        for col in columns: self.table.heading(col, text=col.replace("_", " ").title()); self.table.column(col, width=120)
        self.table.pack(side="left", fill="both", expand=True); self.table.bind("<<TreeviewSelect>>", self.inspect)
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
        if not self.provider or self.info.build_status != "Supported": return messagebox.showwarning("Unavailable", "Connect to the supported RCT.EXE build first.")
        if self.engine is None or self.engine.provider.info.pid != self.info.pid: self.engine = SearchEngine(self.provider, lambda done,total: self.after(0, lambda: self.progress.configure(value=(done / total * 100) if total else 0)))
        mode = self.mode.get(); value = int(self.value.get(), 0) if mode not in ("unknown",) else None
        self.progress.configure(value=0); self.engine.cancel.clear(); threading.Thread(target=self._scan_thread, args=(mode, value), daemon=True).start()
    def _scan_thread(self, mode, value):
        self.engine.scan(mode, value, [self.typevar.get()], value or 0 if mode.endswith("_by") else 0); self.after(0, self.populate)
    def cancel_scan(self):
        if self.engine: self.engine.cancel.set()
    def populate(self):
        self.table.delete(*self.table.get_children())
        if self.engine and self.engine.baseline:
            self.count.set("Unknown baseline captured; perform a transition, then filter")
        else:
            self.count.set(f"Candidates: {len(self.engine.candidates) if self.engine else 0}")
        for index, c in enumerate(self.engine.candidates if self.engine else []): self.table.insert("", "end", iid=str(index), values=(f"0x{c.address:08x}", f"+0x{c.relative:x}", c.type_name, c.current, c.previous, c.delta, c.label, c.status))
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
        c = self.selected()[0]; label = f"Candidate 0x{c.relative:x}"; loc = {"id": f"candidate_{c.relative:x}", "label": label, "module": "RCT.EXE", "offset": f"0x{c.relative:x}", "type": c.type_name, "status": "candidate", "confidence": "low", "build_hash": self.info.build_hash, "notes": "Saved from GUI scan", "date_discovered": datetime.now(timezone.utc).date().isoformat(), "date_last_validated": None}
        MetadataStore().save_location(self.info.build_hash, loc); messagebox.showinfo("Bookmark saved", f"Saved {label} to {METADATA_PATH}")
    def watch_selected(self):
        for c in self.selected():
            if c not in self.watches: self.watches.append(c)
    def refresh_watches(self):
        if not self.provider: return
        for c in self.watches:
            try: c.previous, c.current = c.current, interpret(self.provider.read(c.address, TYPES[c.type_name][0]), c.type_name)
            except OSError: pass
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
