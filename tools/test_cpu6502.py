#!/usr/bin/env python3

from __future__ import annotations

import unittest

from tools.emu.cpu6502 import Cpu6502, FLAG_C, FLAG_N, FLAG_V, FLAG_Z


class Cpu6502Tests(unittest.TestCase):
    def cpu_with(self, code: bytes, address: int = 0x2000) -> Cpu6502:
        memory = bytearray(0x10000)
        memory[address : address + len(code)] = code
        cpu = Cpu6502(memory)
        cpu.pc = address
        return cpu

    def test_adc_and_flags(self) -> None:
        cpu = self.cpu_with(bytes.fromhex("A9 7F 18 69 01"))
        for _ in range(3): cpu.step()
        self.assertEqual(cpu.a, 0x80)
        self.assertTrue(cpu.p & FLAG_N)
        self.assertTrue(cpu.p & FLAG_V)
        self.assertFalse(cpu.p & FLAG_C)
        self.assertFalse(cpu.p & FLAG_Z)

    def test_jsr_rts(self) -> None:
        cpu = self.cpu_with(bytes.fromhex("20 06 20 A9 42 EA A9 11 60"))
        cpu.step()
        self.assertEqual(cpu.pc, 0x2006)
        cpu.step(); cpu.step()
        self.assertEqual(cpu.pc, 0x2003)
        cpu.step()
        self.assertEqual(cpu.a, 0x42)

    def test_zero_page_index_wrap(self) -> None:
        cpu = self.cpu_with(bytes.fromhex("A2 02 B5 FF"))
        cpu.memory[0x0001] = 0x77
        cpu.step(); cpu.step()
        self.assertEqual(cpu.a, 0x77)


if __name__ == "__main__":
    unittest.main()

