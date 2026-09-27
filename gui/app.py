#!/usr/bin/env python3
import csv
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime, timezone
from .rct1_gui import *

MAX_DISPLAY_ROWS = 5_000
CONTINUOUS_MODES = {"changed", "unchanged", "increased", "decreased", "increased_by", "decreased_by"}

def format_hex_grid(data, start, display_bits):
    width = display_bits // 8
    bit_header = " ".join(str(bit) for bit in range(display_bits - 1, -1, -1))
    lines = [f"{display_bits}-bit little-endian view; bit positions: {bit_header}",
             "Address        " + "  ".join(f"+0x{i:04x}" for i in range(0, 16, width))]
    for row_start in range(0, len(data), 16):
        cells = []
        for offset in range(row_start, min(row_start + 16, len(data)), width):
            chunk = data[offset:offset + width]
            if len(chunk) < width:
                cells.append("".ljust(display_bits // 4)); continue
            cells.append(f"{int.from_bytes(chunk, 'little'):0{display_bits // 4}x}")
        lines.append(f"0x{start + row_start:08x}  " + "  ".join(cells))
    return "\n".join(lines)

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("RCT1 Read-Only Memory Research"); self.geometry("1180x760")
        self.info = None; self.provider = None; self.engine = None; self.watches = []; self.watch_keys = set()
        self.scanning = False
        self.continuous = tk.BooleanVar(value=False)
        self.continuous_job = None
        self.sort_column = None
        self.sort_reverse = False
        self.undo_stack = []
        self.redo_stack = []
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
        ttk.Button(controls, text="Choose region", command=self.choose_region).pack(side="left", padx=4)
        self.scan_button = ttk.Button(controls, text="Run scan/filter", command=self.run_scan); self.scan_button.pack(side="left", padx=4)
        ttk.Button(controls, text="Cancel", command=self.cancel_scan).pack(side="left", padx=4)
        ttk.Button(controls, text="Clear/New scan", command=self.clear_scan).pack(side="left", padx=4)
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
        ttk.Button(bottom, text="Typed memory view", command=self.view_selected_memory).pack(side="left", padx=3)
        ttk.Button(bottom, text="Memory browser", command=self.open_memory_browser).pack(side="left", padx=3)
        ttk.Button(bottom, text="Watch selected", command=self.watch_selected).pack(side="left", padx=3)
        ttk.Button(bottom, text="Refresh watches", command=self.refresh_watches).pack(side="left", padx=3)
        ttk.Button(bottom, text="Save session", command=self.save_session).pack(side="left", padx=3)
        ttk.Button(bottom, text="Load session", command=self.load_session).pack(side="left", padx=3)
        ttk.Button(bottom, text="Review bookmarks", command=self.review_bookmarks).pack(side="left", padx=3)
        ttk.Button(bottom, text="Undo", command=self.undo).pack(side="left", padx=3)
        ttk.Button(bottom, text="Redo", command=self.redo).pack(side="left", padx=3)
        ttk.Button(bottom, text="Export candidates", command=self.export_candidates).pack(side="left", padx=3)
        self.inspector = tk.StringVar(value="Select a candidate for read-only neighborhood inspection."); ttk.Label(bottom, textvariable=self.inspector).pack(side="left", padx=15)
    def refresh_status(self):
        old = self.info.pid if self.info else None
        self.info = find_process(); self.provider = MemoryProvider(self.info) if self.info else None
        if not self.info:
            self.status_text.set("RCT1: DISCONNECTED\nMemory Access: unavailable\nScan: idle"); self.state_text.set("Unavailable"); self.after(1500, self.refresh_status); return
        changed = old is not None and old != self.info.pid
        if changed:
            self.undo_stack.clear(); self.redo_stack.clear()
            self.engine = None; self.watches.clear(); self.watch_keys.clear()
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
        before = self.engine.snapshot()
        self.progress.configure(value=0); self.engine.cancel.clear(); self.scanning = True; self.scan_button.configure(state="disabled")
        threading.Thread(target=self._scan_thread, args=(mode, value, scan_start, scan_end, before), daemon=True).start()
    def _scan_thread(self, mode, value, scan_start, scan_end, before):
        try:
            self.engine.scan(mode, value, [self.typevar.get()], value or 0 if mode.endswith("_by") else 0, scan_start, scan_end)
            self.after(0, lambda: self.finish_scan(mode, before))
        except Exception as error:
            self.after(0, lambda: self.scan_failed(error))
    def cancel_scan(self):
        self.continuous.set(False)
        if self.continuous_job is not None:
            self.after_cancel(self.continuous_job); self.continuous_job = None
        if self.engine: self.engine.cancel.set()
    def clear_scan(self):
        has_results = self.engine and (self.engine.candidates or self.engine.baseline or self.watch_keys)
        if has_results and not messagebox.askyesno("Clear scan", "Clear candidates, baseline, history, and watched rows?", parent=self): return
        self.cancel_scan()
        self.engine = SearchEngine(self.provider) if self.provider else None
        self.undo_stack.clear(); self.redo_stack.clear()
        self.watches.clear(); self.watch_keys.clear(); self.table.delete(*self.table.get_children())
        self.count.set("Candidates: 0"); self.inspector.set("Select a candidate for read-only neighborhood inspection.")
    def finish_scan(self, mode, before):
        if self.engine and not self.engine.cancel.is_set():
            self.undo_stack.append(before); self.undo_stack = self.undo_stack[-8:]; self.redo_stack.clear()
        self.populate(mode)
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
    def undo(self):
        if self.scanning or not self.engine or not self.undo_stack: return
        self.redo_stack.append(self.engine.snapshot())
        self.engine.restore(self.undo_stack.pop()); self.populate()
    def redo(self):
        if self.scanning or not self.engine or not self.redo_stack: return
        self.undo_stack.append(self.engine.snapshot())
        self.engine.restore(self.redo_stack.pop()); self.populate()
    def export_candidates(self):
        if not self.engine or not self.engine.candidates: return messagebox.showinfo("Export", "There are no candidates to export.")
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json"), ("CSV", "*.csv")])
        if not path: return
        candidates = [asdict(candidate) for candidate in self.engine.candidates]
        if path.lower().endswith(".csv"):
            fields = ["address", "relative", "type_name", "current", "previous", "delta", "history", "label", "status"]
            with open(path, "w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
                for item in candidates:
                    item["history"] = ",".join(str(value) for value in item["history"]); writer.writerow({key: item.get(key, "") for key in fields})
        else:
            payload = {"version": 1, "pid": self.info.pid, "base": self.info.base, "build_hash": self.info.build_hash, "candidates": candidates}
            Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        messagebox.showinfo("Export", f"Exported {len(candidates):,} candidates.")
    def choose_region(self):
        if not self.provider or not self.info: return messagebox.showwarning("Region", "Connect to RCT first.")
        window = tk.Toplevel(self); window.title("Choose Readable Private Region"); window.geometry("760x360"); window.transient(self)
        columns = ("start", "end", "relative", "size")
        table = ttk.Treeview(window, columns=columns, show="headings", selectmode="browse")
        for column in columns: table.heading(column, text=column.title()); table.column(column, width=150)
        table.pack(fill="both", expand=True, padx=8, pady=8)
        mappings = self.provider.mappings()
        for index, (start, end) in enumerate(mappings):
            table.insert("", "end", iid=str(index), values=(f"0x{start:08x}", f"0x{end:08x}", f"+0x{start - self.info.base:x}", f"{end - start:,} bytes"))
        def choose():
            selected = table.selection()
            if not selected: return
            start, end = mappings[int(selected[0])]
            self.range_start.delete(0, tk.END); self.range_start.insert(0, hex(start - self.info.base))
            self.range_end.delete(0, tk.END); self.range_end.insert(0, hex(end - self.info.base)); window.destroy()
        buttons = ttk.Frame(window); buttons.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(buttons, text="Use selected region", command=choose).pack(side="left", padx=3)
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right", padx=3)
    def selected(self):
        return [self.engine.candidates[int(x)] for x in self.table.selection()]
    def inspect(self, _event=None):
        selected = self.selected()
        if selected and self.provider:
            c = selected[0]
            try: data = self.provider.read(max(0, c.address - 16), 32); self.inspector.set(f"0x{c.address:08x} (+0x{c.relative:x})  {data.hex(' ')}  [read-only neighborhood ±16 bytes]")
            except OSError: self.inspector.set("Selected address is unavailable (process may have restarted).")
    def view_selected_memory(self):
        selected = self.selected()
        if not selected or not self.provider:
            return messagebox.showinfo("Typed memory view", "Select a candidate first.")
        candidate = selected[0]
        self.open_memory_view(candidate.address, candidate.relative, candidate.label or candidate.type_name)
    def open_memory_view(self, address, relative, label=""):
        window = tk.Toplevel(self); window.title("RCT1 Typed Memory Viewer"); window.geometry("980x620"); window.transient(self)
        header = tk.StringVar(); timestamp = tk.StringVar()
        ttk.Label(window, textvariable=header, justify="left").pack(anchor="w", padx=8, pady=(8, 2))
        ttk.Label(window, textvariable=timestamp).pack(anchor="w", padx=8, pady=(0, 5))
        controls = ttk.Frame(window); controls.pack(fill="x", padx=8, pady=3)
        radius = tk.IntVar(value=16); live = tk.BooleanVar(value=True); display_bits = tk.IntVar(value=8); live_job = [None]
        ttk.Label(controls, text="Bytes around address:").pack(side="left")
        radius_box = ttk.Combobox(controls, textvariable=radius, values=[8, 16, 32], state="readonly", width=5); radius_box.pack(side="left", padx=4)
        ttk.Label(controls, text="Grid:").pack(side="left", padx=(12, 2))
        for bits in (8, 16, 32): ttk.Radiobutton(controls, text=f"{bits}-bit", variable=display_bits, value=bits).pack(side="left", padx=2)
        notebook = ttk.Notebook(window); notebook.pack(fill="both", expand=True, padx=8, pady=5)
        decoded_frame = ttk.Frame(notebook); grid_frame = ttk.Frame(notebook)
        notebook.add(decoded_frame, text="Decoded values"); notebook.add(grid_frame, text="Hex grid")
        table = ttk.Treeview(decoded_frame, columns=("offset", "address", "byte", "ascii", "u8", "s8", "u16", "s16", "u32", "s32"), show="headings")
        headings = {"offset": "Offset", "address": "Address", "byte": "Byte", "ascii": "ASCII", "u8": "u8", "s8": "s8", "u16": "u16 LE", "s16": "s16 LE", "u32": "u32 LE", "s32": "s32 LE"}
        for column in table["columns"]:
            table.heading(column, text=headings[column]); table.column(column, width=88, anchor="center")
        table.column("address", width=115); table.column("byte", width=70); table.column("ascii", width=65)
        table.pack(fill="both", expand=True, padx=8, pady=5)
        grid = tk.Text(grid_frame, wrap="none", font=("Courier New", 10), state="disabled", background="#f4f4f4")
        grid.pack(fill="both", expand=True, padx=5, pady=5)
        def refresh():
            if not self.info or not self.provider or self.info.pid != self.provider.info.pid:
                header.set("Process unavailable or restarted; close this viewer."); return
            start = max(0, address - radius.get()); size = radius.get() * 2 + 16
            try: data = self.provider.read(start, size)
            except OSError:
                header.set("Selected address is unavailable (process may have restarted)."); return
            header.set(f"{label or 'Memory'}   address 0x{address:08x}   relative +0x{relative:x}\nPID {self.info.pid}   module base 0x{self.info.base:08x}   read-only")
            timestamp.set(f"Refreshed {datetime.now(timezone.utc).isoformat(timespec='seconds')}   ({len(data)} bytes; interpretations are little-endian)")
            table.delete(*table.get_children())
            for row in typed_memory_rows(data):
                absolute = start + int(row["offset"])
                table.insert("", "end", values=(f"{int(row['offset']) - (address - start):+d}", f"0x{absolute:08x}", row["byte"], row["ascii"], row["u8"], row["s8"], row["u16"], row["s16"], row["u32"], row["s32"]))
            grid.configure(state="normal"); grid.delete("1.0", tk.END); grid.insert("1.0", format_hex_grid(data, start, display_bits.get())); grid.configure(state="disabled")
            if live.get(): live_job[0] = window.after(250, refresh)
        def toggle_live():
            if live.get(): refresh()
            elif live_job[0] is not None:
                window.after_cancel(live_job[0]); live_job[0] = None
        def refresh_from_control(_event=None):
            if live_job[0] is not None: window.after_cancel(live_job[0]); live_job[0] = None
            refresh()
        def close():
            if live_job[0] is not None: window.after_cancel(live_job[0])
            window.destroy()
        ttk.Button(controls, text="Refresh", command=refresh_from_control).pack(side="left", padx=4)
        ttk.Checkbutton(controls, text="Live refresh (250 ms)", variable=live, command=toggle_live).pack(side="left", padx=4)
        ttk.Button(controls, text="Close", command=close).pack(side="right", padx=4)
        radius_box.bind("<<ComboboxSelected>>", refresh_from_control)
        window.protocol("WM_DELETE_WINDOW", close); refresh()
    def open_memory_browser(self):
        if not self.info or not self.provider or self.info.build_status != "Supported":
            return messagebox.showwarning("Memory browser", "Connect to the supported RCT.EXE build first.")
        mappings = self.provider.mappings()
        if not mappings:
            return messagebox.showinfo("Memory browser", "No readable private memory regions are available.")
        window = tk.Toplevel(self); window.title("RCT1 Read-Only Memory Browser"); window.geometry("1050x650"); window.transient(self)
        region_var = tk.StringVar(); address_var = tk.StringVar(); page_var = tk.IntVar(value=4096); bits_var = tk.IntVar(value=8); live = tk.BooleanVar(value=True); live_job = [None]
        region_values = [f"0x{start:08x} - 0x{end:08x} ({end - start:,} bytes)" for start, end in mappings]
        region_var.set(region_values[0]); address_var.set(hex(mappings[0][0]))
        header = tk.StringVar(); timestamp = tk.StringVar()
        top = ttk.Frame(window); top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="Region:").pack(side="left")
        region_box = ttk.Combobox(top, textvariable=region_var, values=region_values, state="readonly", width=38); region_box.pack(side="left", padx=4)
        ttk.Label(top, text="Address:").pack(side="left", padx=(10, 2)); address_entry = ttk.Entry(top, textvariable=address_var, width=13); address_entry.pack(side="left")
        ttk.Label(top, text="Page:").pack(side="left", padx=(10, 2)); page_box = ttk.Combobox(top, textvariable=page_var, values=[256, 4096, 16384], state="readonly", width=7); page_box.pack(side="left")
        ttk.Label(top, text="Grid:").pack(side="left", padx=(10, 2))
        for bits in (8, 16, 32): ttk.Radiobutton(top, text=str(bits), variable=bits_var, value=bits).pack(side="left", padx=2)
        ttk.Label(window, textvariable=header, justify="left").pack(anchor="w", padx=8)
        ttk.Label(window, textvariable=timestamp).pack(anchor="w", padx=8, pady=(0, 3))
        grid = tk.Text(window, wrap="none", font=("Courier New", 10), state="disabled", background="#f4f4f4"); grid.pack(fill="both", expand=True, padx=8, pady=5)
        def selected_region(): return mappings[region_values.index(region_var.get())]
        def refresh():
            if not self.info or not self.provider or self.info.pid != self.provider.info.pid:
                header.set("Process unavailable or restarted; close this browser."); return
            region_start, region_end = selected_region()
            try: requested = int(address_var.get().strip(), 0)
            except ValueError:
                header.set("Enter a valid hexadecimal or decimal address."); return
            start = min(max(requested, region_start), max(region_start, region_end - 1)); size = min(page_var.get(), region_end - start)
            try: data = self.provider.read(start, size)
            except OSError:
                header.set("Memory page is unavailable (process may have restarted)."); return
            address_var.set(hex(start)); header.set(f"Region 0x{region_start:08x}-0x{region_end:08x}   showing 0x{start:08x}-0x{start + len(data):08x}\nPID {self.info.pid}   module base 0x{self.info.base:08x}   read-only")
            timestamp.set(f"Refreshed {datetime.now(timezone.utc).isoformat(timespec='seconds')}   ({len(data):,} bytes)")
            grid.configure(state="normal"); grid.delete("1.0", tk.END); grid.insert("1.0", format_hex_grid(data, start, bits_var.get())); grid.configure(state="disabled")
            if live.get(): live_job[0] = window.after(250, refresh)
        def cancel_timer():
            if live_job[0] is not None: window.after_cancel(live_job[0]); live_job[0] = None
        def control_refresh(_event=None): cancel_timer(); refresh()
        def move_page(amount):
            start, end = selected_region(); current = int(address_var.get(), 0); address_var.set(hex(min(max(start, current + amount * page_var.get()), max(start, end - 1)))); control_refresh()
        def choose_region(_event=None): address_var.set(hex(selected_region()[0])); control_refresh()
        def toggle_live(): cancel_timer(); refresh() if live.get() else None
        def close(): cancel_timer(); window.destroy()
        buttons = ttk.Frame(window); buttons.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(buttons, text="Previous page", command=lambda: move_page(-1)).pack(side="left", padx=3)
        ttk.Button(buttons, text="Next page", command=lambda: move_page(1)).pack(side="left", padx=3)
        ttk.Button(buttons, text="Go", command=control_refresh).pack(side="left", padx=3)
        ttk.Button(buttons, text="Refresh", command=control_refresh).pack(side="left", padx=3)
        ttk.Checkbutton(buttons, text="Live refresh (250 ms)", variable=live, command=toggle_live).pack(side="left", padx=8)
        ttk.Button(buttons, text="Close", command=close).pack(side="right", padx=3)
        region_box.bind("<<ComboboxSelected>>", choose_region); page_box.bind("<<ComboboxSelected>>", control_refresh); address_entry.bind("<Return>", control_refresh)
        window.protocol("WM_DELETE_WINDOW", close); refresh()
    def bookmark(self):
        if not self.info or self.info.build_status != "Supported" or not self.selected(): return
        store = MetadataStore(); data = store.load(); locations = data.get("builds", {}).get(self.info.build_hash, {}).get("locations", [])
        saved = []
        for c in self.selected():
            bookmark_id = f"candidate_{c.relative:x}"
            existing = next((item for item in locations if item.get("id") == bookmark_id), {})
            details = self.edit_bookmark(existing, c)
            if details is None: break
            today = datetime.now(timezone.utc).date().isoformat()
            loc = {"id": bookmark_id, "label": details["label"], "module": "RCT.EXE", "offset": f"0x{c.relative:x}", "type": c.type_name,
                   "status": details["status"], "confidence": details["confidence"], "build_hash": self.info.build_hash,
                   "notes": details["notes"], "date_discovered": existing.get("date_discovered", today),
                   "date_last_validated": today if details["status"] == "validated" else existing.get("date_last_validated")}
            store.save_location(self.info.build_hash, loc); saved.append(details["label"])
        if saved: messagebox.showinfo("Bookmarks saved", f"Saved {len(saved)} bookmark(s) to {METADATA_PATH}")
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
    def review_bookmarks(self):
        if not self.info or self.info.build_status != "Supported":
            return messagebox.showwarning("Bookmarks", "Connect to the supported RCT.EXE build first.")
        data = MetadataStore().load()
        locations = data.get("builds", {}).get(self.info.build_hash, {}).get("locations", [])
        window = tk.Toplevel(self); window.title("RCT1 Bookmarks"); window.geometry("1050x420"); window.transient(self)
        columns = ("label", "address", "relative", "type", "current", "status", "confidence", "notes")
        table = ttk.Treeview(window, columns=columns, show="headings", selectmode="browse")
        for column in columns:
            table.heading(column, text=column.replace("_", " ").title())
            table.column(column, width=130 if column not in ("notes", "label") else 220)
        table.pack(fill="both", expand=True, padx=8, pady=8)
        def refresh():
            table.delete(*table.get_children())
            for index, location in enumerate(locations):
                offset = int(location["offset"], 16); address = resolve_address(self.info.base, offset)
                try:
                    raw = interpret(self.provider.read(address, TYPES[location["type"]][0]), location["type"])
                    current = format_cash(raw) if location.get("scale") == "raw / 10" else str(raw)
                except (KeyError, OSError): current = "unavailable"
                table.insert("", "end", iid=str(index), values=(location.get("label", ""), f"0x{address:08x}", f"+0x{offset:x}", location.get("type", ""), current, location.get("status", ""), location.get("confidence", ""), location.get("notes", "")))
        def view_selected():
            selection = table.selection()
            if not selection: return
            location = locations[int(selection[0])]
            offset = int(location["offset"], 16)
            self.open_memory_view(resolve_address(self.info.base, offset), offset, location.get("label", "Bookmark"))
        def edit_selected():
            selection = table.selection()
            if not selection: return
            location = locations[int(selection[0])]
            candidate = Candidate(resolve_address(self.info.base, int(location["offset"], 16)), int(location["offset"], 16), location["type"], 0, 0)
            details = self.edit_bookmark(location, candidate)
            if details is None: return
            today = datetime.now(timezone.utc).date().isoformat()
            location.update(details)
            if details["status"] == "validated": location["date_last_validated"] = today
            MetadataStore().save_location(self.info.build_hash, location); refresh()
        buttons = ttk.Frame(window); buttons.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(buttons, text="Refresh", command=refresh).pack(side="left", padx=3)
        ttk.Button(buttons, text="Typed memory view", command=view_selected).pack(side="left", padx=3)
        ttk.Button(buttons, text="Edit selected", command=edit_selected).pack(side="left", padx=3)
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right", padx=3)
        refresh()
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
                self.engine = SearchEngine(self.provider); self.engine.load_session(Path(path)); self.undo_stack.clear(); self.redo_stack.clear(); self.populate()
            except (OSError, ValueError, json.JSONDecodeError) as error:
                messagebox.showerror("Session load failed", str(error))

def main(): App().mainloop()
