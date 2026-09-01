#!/usr/bin/env python3
"""Regression coverage for the verified opening-route state changes."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.d64 import D64Image
from tools.trace_e1_opening import trace_opening


ROOT = Path(__file__).resolve().parents[1]


class E1OpeningTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report, cls.modules = trace_opening(
            (ROOT / "extracted/e1/e1_room0_ready_memory.bin").read_bytes(),
            D64Image.read(ROOT / "intake/NEUROMA0.D64"),
        )

    def test_extracts_pax_overlay_chain(self) -> None:
        self.assertEqual(len(self.modules["pax_root"]), 2486)
        self.assertEqual(len(self.modules["pax_bank"]), 1064)
        self.assertEqual(len(self.modules["pax_send_message"]), 2909)
        self.assertEqual(
            self.report["sources"]["pax_root"]["sha256"],
            "2b94ea84a932ec609f8415b7f1636862b29c7573fa603d35ffb5d762870e122e",
        )

    def test_executes_required_money_route(self) -> None:
        events = self.report["routes"]["required"]
        self.assertEqual((events[0]["cash"], events[0]["bank"]), (6, 2000))
        self.assertEqual((events[3]["cash"], events[3]["bank"]), (46, 1960))
        self.assertEqual((events[5]["cash"], events[5]["bank"]), (0, 1960))

    def test_executes_optional_armitage_deposit(self) -> None:
        deposit = self.report["routes"]["armitage_optional"][1]
        self.assertEqual(deposit["amount"], 10000)
        self.assertEqual((deposit["cash"], deposit["bank"]), (46, 11960))

    def test_teardown_and_boundary_are_explicit(self) -> None:
        self.assertEqual(self.report["executed_code"]["room0_teardown"]["bytes"], "60")
        self.assertIn("location selector", self.report["boundary"]["open"])

    def test_checked_in_artifact_matches(self) -> None:
        checked = json.loads(
            (ROOT / "extracted/e1/e1_opening_route_trace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(checked, self.report)


if __name__ == "__main__":
    unittest.main()
