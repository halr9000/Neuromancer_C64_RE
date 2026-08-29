"""Regression coverage for deterministic E1 room-0 vector execution."""

from __future__ import annotations

import unittest
from pathlib import Path

from tools.trace_e1_room0 import trace_room0


ROOT = Path(__file__).resolve().parents[1]
ROOM0 = ROOT / "extracted/e1/e1_room0_ready_memory.bin"


class E1Room0RuntimeTraceTests(unittest.TestCase):
    def test_room0_vectors_execute_deterministically(self) -> None:
        report = trace_room0(ROOM0, 64)

        self.assertEqual(report["room_vectors"], {
            "0xF00A": "0xF0F6",
            "0xF00D": "0xF10E",
            "0xF010": "0xF10D",
        })
        self.assertEqual(report["init"]["instructions"], 13)
        self.assertEqual(report["init"]["changed"], {
            "0x0003": 0x22,
            "0x0007": 0x24,
            "0x0014": 0x33,
            "0x0018": 0x42,
        })
        self.assertEqual(report["tick_instruction_total"], 1276)
        self.assertEqual(len(report["tick_state_changes"]), 64)
        self.assertEqual(report["teardown"]["instructions"], 2)
        self.assertEqual(report["entity_dispatcher_inactive_path"]["instructions"], 24)
        self.assertEqual(report["entity_dispatcher_inactive_path"]["room_data_root_saved"], {
            "low": "0x48",
            "high": "0xF2",
        })
        self.assertEqual(
            report["entity_dispatcher_inactive_path"]["executed_addresses"],
            [
                "0x6429", "0x642C", "0x642F", "0x6432", "0x6434", "0x6437",
                "0x6439", "0x643B", "0x6463", "0x6466", "0x6468", "0x6C8C",
                "0x6C8F", "0x6C92",
            ],
        )
        self.assertEqual(
            report["output_memory_sha256"],
            "f1006c2fa4c38ca6b6836d8a547f55b2779dc84c7ef65ddd077fcc912eff9387",
        )


if __name__ == "__main__":
    unittest.main()
