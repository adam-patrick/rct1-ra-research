#!/usr/bin/env python3
"""Thin, external, read-only RCT1 memory research tool.

The backend deliberately exposes reads only. There is no process-memory write
API in this module.
"""
from __future__ import annotations

import ctypes
import copy
import hashlib
import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable

SUPPORTED_BUILD = "bdfebd64383b231de0252fe0726523d1c45aa2c4da919c2d7ed8bfb7aaa05c76"
ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "gui" / "research_metadata.json"

TYPES = {"s8": (1, True), "u8": (1, False), "s16": (2, True),
         "u16": (2, False), "s32": (4, True), "u32": (4, False)}
MAX_CANDIDATES = 50_000
MAX_BASELINE_BYTES = 256 * 1024 * 1024

@dataclass
class ProcessInfo:
    pid: int
    path: str
    base: int
    build_hash: str | None
    build_status: str

@dataclass
class Candidate:
    address: int
    relative: int
    type_name: str
    current: int
    previous: int
    label: str = ""
    status: str = "candidate"
    history: list[int] = field(default_factory=list)

    def __post_init__(self):
        if not self.history:
            self.history = [self.current] if self.current == self.previous else [self.previous, self.current]

    @property
    def delta(self) -> int:
        return self.current - self.previous

def interpret(data: bytes, type_name: str) -> int:
    width, signed = TYPES[type_name]
    return int.from_bytes(data[:width], "little", signed=signed)

def resolve_address(base: int, offset: int) -> int:
    return base + offset

def format_cash(raw: int) -> str:
    return f"${raw / 10:,.2f}"

def _pid_list() -> Iterable[int]:
    for entry in os.listdir("/proc"):
        if entry.isdigit():
            yield int(entry)

def _module(pid: int) -> tuple[int, str]:
    base = 0
    path = ""
    with open(f"/proc/{pid}/maps", encoding="utf-8") as stream:
        for line in stream:
            fields = line.rstrip().split(None, 5)
            if len(fields) < 5 or "/RCT.EXE" not in line:
                continue
            start, _ = (int(x, 16) for x in fields[0].split("-"))
            file_offset = int(fields[2], 16)
            if file_offset == 0:
                base = start
                path = fields[5] if len(fields) == 6 else ""
                break
    return base, path

def find_process() -> ProcessInfo | None:
    for pid in _pid_list():
        try:
            with open(f"/proc/{pid}/comm", encoding="utf-8") as stream:
                if stream.read().strip() != "RCT.EXE":
                    continue
            base, mapped_path = _module(pid)
            exe = os.readlink(f"/proc/{pid}/exe")
            path = mapped_path or exe
            digest = None
            if path and os.path.isfile(path):
                digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            status = "Supported" if digest == SUPPORTED_BUILD else ("Unknown" if digest is None else "Unsupported")
            return ProcessInfo(pid, path or exe, base, digest, status)
        except (FileNotFoundError, PermissionError, OSError, ValueError):
            continue
    return None

class MemoryProvider:
    """Read-only process memory provider using process_vm_readv only."""
    def __init__(self, info: ProcessInfo):
        self.info = info
        self._libc = ctypes.CDLL(None, use_errno=True)
        self._libc.process_vm_readv.argtypes = [ctypes.c_int, ctypes.c_void_p,
            ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong]
        self._libc.process_vm_readv.restype = ctypes.c_ssize_t

    def read(self, address: int, size: int) -> bytes:
        local = ctypes.create_string_buffer(size)
        class IOVec(ctypes.Structure):
            _fields_ = [("base", ctypes.c_void_p), ("length", ctypes.c_size_t)]
        local_iov = IOVec(ctypes.cast(local, ctypes.c_void_p), size)
        remote_iov = IOVec(ctypes.c_void_p(address), size)
        got = self._libc.process_vm_readv(self.info.pid, ctypes.byref(local_iov), 1,
                                          ctypes.byref(remote_iov), 1, 0)
        if got != size:
            raise OSError(ctypes.get_errno(), "short or failed process_vm_readv")
        return local.raw

    def mappings(self) -> list[tuple[int, int]]:
        ranges = []
        with open(f"/proc/{self.info.pid}/maps", encoding="utf-8") as stream:
            for line in stream:
                fields = line.split()
                if len(fields) < 5 or not fields[1].startswith("r") or fields[1][3] != "p":
                    continue
                lo, hi = (int(x, 16) for x in fields[0].split("-"))
                if lo < 0x10000000 and hi > 0x00400000:
                    ranges.append((lo, hi))
        return ranges

class SearchEngine:
    def __init__(self, provider: MemoryProvider, progress: Callable[[int, int], None] | None = None):
        self.provider, self.progress = provider, progress or (lambda *_: None)
        self.candidates: list[Candidate] = []
        self.baseline: list[tuple[int, bytes]] = []
        self.baseline_types: list[str] = []
        self.cancel = threading.Event()
        self.truncated = False
        self.scan_message = ""

    def scan(self, mode: str, value: int | None = None, type_names: list[str] | None = None,
             delta: int = 0, scan_start: int | None = None, scan_end: int | None = None):
        types = type_names or list(TYPES)
        absolute_start, absolute_end = self._absolute_range(scan_start, scan_end)
        ranges = self.provider.mappings()
        if absolute_start is not None or absolute_end is not None:
            absolute_start = absolute_start if absolute_start is not None else 0
            ranges = [(max(lo, absolute_start), min(hi, absolute_end) if absolute_end is not None else hi)
                      for lo, hi in ranges]
            ranges = [(lo, hi) for lo, hi in ranges if hi > lo]
        self.truncated = False
        self.scan_message = ""
        if mode == "unknown":
            # Keep the paused snapshot as bytes. Materialising one Python
            # Candidate per address can mean millions of objects and makes an
            # unknown baseline look like a hung GUI. Candidates are generated
            # only after the next comparison, when the search has narrowed.
            self.candidates = []
            self.baseline = []
            self.baseline_types = types
            captured = 0
            for lo, hi in ranges:
                for address in range(lo, hi, 1024 * 1024):
                    if self.cancel.is_set(): return
                    if captured >= MAX_BASELINE_BYTES:
                        self.truncated = True
                        self.scan_message = f"Baseline limited to {MAX_BASELINE_BYTES // (1024 * 1024)} MiB"
                        return
                    end = min(address + 1024 * 1024, hi)
                    end = min(end, address + MAX_BASELINE_BYTES - captured)
                    try: data = self.provider.read(address, end - address)
                    except OSError: continue
                    self.baseline.append((address, data))
                    captured += len(data)
                    self.progress(address - lo, hi - lo)
            return
        if mode == "exact":
            self.candidates = []
            self.baseline = []
            for lo, hi in ranges:
                for address in range(lo, hi, 1024 * 1024):
                    if self.cancel.is_set(): return
                    end = min(address + 1024 * 1024, hi)
                    try: data = self.provider.read(address, end - address)
                    except OSError: continue
                    for name in types:
                        width = TYPES[name][0]
                        for off in range(0, len(data) - width + 1):
                            current = interpret(data[off:off + width], name)
                            if mode == "unknown" or current == value:
                                self.candidates.append(Candidate(address + off, address + off - self.provider.info.base, name, current, current, history=[current]))
                    self.progress(address - lo, hi - lo)
        elif self.baseline and mode == "unchanged":
            # Most memory remains unchanged. Keep the newer snapshot in place
            # and defer candidate creation until a selective filter is used.
            refined = []
            for lo, previous_bytes in self.baseline:
                if self.cancel.is_set(): return
                read_lo = max(lo, absolute_start) if absolute_start is not None else lo
                read_hi = min(lo + len(previous_bytes), absolute_end) if absolute_end is not None else lo + len(previous_bytes)
                if read_hi <= read_lo: continue
                try: current_bytes = self.provider.read(read_lo, read_hi - read_lo)
                except OSError: continue
                refined.append((read_lo, current_bytes))
                self.progress(read_lo, read_hi)
            self.baseline = refined
            self.candidates = []
            self.scan_message = "Unchanged snapshot retained; candidates deferred"
        elif self.baseline:
            kept = []
            stop = False
            for lo, previous_bytes in self.baseline:
                if self.cancel.is_set(): return
                try: current_bytes = self.provider.read(lo, len(previous_bytes))
                except OSError: continue
                for name in self.baseline_types:
                    width = TYPES[name][0]
                    start = max(0, (absolute_start or lo) - lo)
                    end = min(len(previous_bytes), (absolute_end or (lo + len(previous_bytes))) - lo)
                    for off in range(start - (start % width), end - width + 1, width):
                        previous = interpret(previous_bytes[off:off + width], name)
                        current = interpret(current_bytes[off:off + width], name)
                        d = current - previous
                        ok = {"changed": d != 0, "unchanged": d == 0, "increased": d > 0,
                              "decreased": d < 0, "increased_by": d == delta,
                              "decreased_by": d == -delta}.get(mode, False)
                        if ok:
                            kept.append(Candidate(lo + off, lo + off - self.provider.info.base, name, current, previous, history=[previous, current]))
                            if len(kept) >= MAX_CANDIDATES:
                                self.truncated = True
                                self.scan_message = f"Results limited to {MAX_CANDIDATES:,} candidates"
                                stop = True
                                break
                    if stop: break
                self.progress(lo, lo + len(previous_bytes))
                if stop: break
            self.baseline = []
            self.candidates = kept
        else:
            kept = []
            for candidate in self.candidates:
                if self.cancel.is_set(): return
                if absolute_start is not None and candidate.address < absolute_start: continue
                if absolute_end is not None and candidate.address >= absolute_end: continue
                try: current = interpret(self.provider.read(candidate.address, TYPES[candidate.type_name][0]), candidate.type_name)
                except OSError: continue
                d = current - candidate.current
                ok = {"changed": d != 0, "unchanged": d == 0, "increased": d > 0,
                      "decreased": d < 0, "increased_by": d == delta,
                      "decreased_by": d == -delta}.get(mode, False)
                if ok:
                    kept.append(Candidate(candidate.address, candidate.relative, candidate.type_name, current, candidate.current, candidate.label, candidate.status, candidate.history + [current]))
            self.candidates = kept

    def _absolute_range(self, scan_start: int | None, scan_end: int | None) -> tuple[int | None, int | None]:
        start = self.provider.info.base + scan_start if scan_start is not None else None
        end = self.provider.info.base + scan_end if scan_end is not None else None
        if start is not None and end is not None and end <= start:
            raise ValueError("scan range end must be greater than scan range start")
        return start, end

    def snapshot(self) -> dict:
        return {"candidates": copy.deepcopy(self.candidates), "baseline": list(self.baseline),
                "baseline_types": list(self.baseline_types), "truncated": self.truncated,
                "scan_message": self.scan_message}

    def restore(self, snapshot: dict) -> None:
        self.candidates = copy.deepcopy(snapshot["candidates"])
        self.baseline = list(snapshot["baseline"])
        self.baseline_types = list(snapshot["baseline_types"])
        self.truncated = snapshot["truncated"]
        self.scan_message = snapshot["scan_message"]

    def save_session(self, path: Path) -> None:
        payload = {"version": 1, "pid": self.provider.info.pid, "base": self.provider.info.base,
                   "build_hash": self.provider.info.build_hash,
                   "candidates": [asdict(candidate) for candidate in self.candidates]}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def load_session(self, path: Path) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("build_hash") != self.provider.info.build_hash:
            raise ValueError("session belongs to a different executable build")
        self.candidates = []
        for item in payload.get("candidates", []):
            # Absolute addresses are session observations only. Re-resolve
            # every candidate from its module-relative locator after restart.
            item = dict(item)
            item["address"] = resolve_address(self.provider.info.base, item["relative"])
            self.candidates.append(Candidate(**item))

class MetadataStore:
    def __init__(self, path: Path = METADATA_PATH): self.path = path
    def load(self) -> dict:
        try: return json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError): return {"version": 1, "builds": {}}
    def save_location(self, build_hash: str, location: dict) -> None:
        data = self.load(); data.setdefault("version", 1); data.setdefault("builds", {})
        build = data["builds"].setdefault(build_hash, {"locations": []})
        build["locations"] = [x for x in build.get("locations", []) if x.get("id") != location["id"]]
        build["locations"].append(location)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

def known_locations() -> list[dict]:
    return [{"id": "cash", "label": "Cash", "module": "RCT.EXE", "offset": "0x69c590", "type": "u32", "scale": "raw / 10", "status": "validated", "confidence": "medium"},
            {"id": "guest_count", "label": "Guest Count", "module": "RCT.EXE", "offset": "0x69c9f8", "type": "u16", "scale": "direct", "status": "validated", "confidence": "medium"},
            {"id": "park_rating", "label": "Park Rating", "module": "RCT.EXE", "offset": "0x69ce64", "type": "u16", "scale": "direct", "status": "validated", "confidence": "medium"}]

def read_state(provider: MemoryProvider) -> dict:
    values = {}
    for item in known_locations():
        try: values[item["id"]] = interpret(provider.read(resolve_address(provider.info.base, int(item["offset"], 16)), TYPES[item["type"]][0]), item["type"])
        except OSError: values[item["id"]] = None
    return values

if __name__ == "__main__":
    import gui.app as app
    app.main()
