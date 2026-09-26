import json
import tempfile
import unittest
from pathlib import Path
from gui.rct1_gui import *

class GuiLogicTests(unittest.TestCase):
    def test_interpret_signed_and_unsigned(self):
        self.assertEqual(interpret(b"\xff", "u8"), 255); self.assertEqual(interpret(b"\xff", "s8"), -1)
        self.assertEqual(interpret(b"\xff\xff", "s16"), -1)
    def test_addresses_and_cash(self):
        self.assertEqual(resolve_address(0x400000, 0x69c590), 0xa9c590); self.assertEqual(format_cash(93160), "$9,316.00")
    def test_metadata_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            store = MetadataStore(Path(d) / "meta.json"); store.save_location(SUPPORTED_BUILD, {"id": "x", "offset": "0x10"})
            self.assertEqual(store.load()["builds"][SUPPORTED_BUILD]["locations"][0]["id"], "x")
    def test_candidate_delta(self):
        c = Candidate(1, 1, "u16", 9, 4); self.assertEqual(c.delta, 5)
    def test_session_is_build_scoped(self):
        class Provider:
            info = type("Info", (), {"pid": 7, "base": 0x500000, "build_hash": SUPPORTED_BUILD})()
        with tempfile.TemporaryDirectory() as d:
            engine = SearchEngine(Provider()); engine.candidates = [Candidate(0x20, 0x20, "u16", 3, 2)]
            path = Path(d) / "session.json"; engine.save_session(path)
            restored = SearchEngine(Provider()); restored.load_session(path)
            self.assertEqual(restored.candidates[0].delta, 1)
            self.assertEqual(restored.candidates[0].address, 0x500020)
            payload = json.loads(path.read_text()); payload["build_hash"] = "other"; path.write_text(json.dumps(payload))
            with self.assertRaises(ValueError): restored.load_session(path)

    def test_unknown_baseline_is_deferred(self):
        class Provider:
            info = type("Info", (), {"pid": 7, "base": 0x400000, "build_hash": SUPPORTED_BUILD})()
            def mappings(self): return [(0x400000, 0x400004)]
            def read(self, address, size): return bytes([1, 0, 2, 0])[:size]
        engine = SearchEngine(Provider()); engine.scan("unknown", type_names=["u16"])
        self.assertEqual(engine.candidates, []); self.assertTrue(engine.baseline)

if __name__ == "__main__": unittest.main()
