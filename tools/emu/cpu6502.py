#!/usr/bin/env python3
"""Dependency-free documented-opcode 6502 core for targeted RE execution."""

from __future__ import annotations

try:
    from ..instruction_set import OPCODES
except ImportError:
    from instruction_set import OPCODES


FLAG_C = 0x01
FLAG_Z = 0x02
FLAG_I = 0x04
FLAG_D = 0x08
FLAG_B = 0x10
FLAG_U = 0x20
FLAG_V = 0x40
FLAG_N = 0x80


class CpuError(RuntimeError):
    pass


class Cpu6502:
    def __init__(self, memory: bytearray) -> None:
        if len(memory) != 0x10000:
            raise ValueError("6502 memory must be exactly 64 KiB")
        self.memory = memory
        self.a = 0
        self.x = 0
        self.y = 0
        self.sp = 0xFF
        self.p = FLAG_U
        self.pc = 0
        self.steps = 0

    def get_flag(self, flag: int) -> int:
        return 1 if self.p & flag else 0

    def set_flag(self, flag: int, enabled: bool) -> None:
        if enabled:
            self.p |= flag
        else:
            self.p &= ~flag
        self.p |= FLAG_U

    def set_nz(self, value: int) -> int:
        value &= 0xFF
        self.set_flag(FLAG_Z, value == 0)
        self.set_flag(FLAG_N, bool(value & 0x80))
        return value

    def fetch(self) -> int:
        value = self.memory[self.pc]
        self.pc = (self.pc + 1) & 0xFFFF
        return value

    def read_word(self, address: int) -> int:
        low = self.memory[address & 0xFFFF]
        high = self.memory[(address + 1) & 0xFFFF]
        return low | high << 8

    def read_word_zp(self, address: int) -> int:
        low = self.memory[address & 0xFF]
        high = self.memory[(address + 1) & 0xFF]
        return low | high << 8

    def push(self, value: int) -> None:
        self.memory[0x0100 | self.sp] = value & 0xFF
        self.sp = (self.sp - 1) & 0xFF

    def pop(self) -> int:
        self.sp = (self.sp + 1) & 0xFF
        return self.memory[0x0100 | self.sp]

    def address(self, mode: str) -> int:
        if mode == "imm":
            address = self.pc
            self.pc = (self.pc + 1) & 0xFFFF
            return address
        if mode == "zp": return self.fetch()
        if mode == "zpx": return (self.fetch() + self.x) & 0xFF
        if mode == "zpy": return (self.fetch() + self.y) & 0xFF
        if mode == "abs":
            low = self.fetch(); high = self.fetch(); return low | high << 8
        if mode == "absx":
            low = self.fetch(); high = self.fetch(); return ((low | high << 8) + self.x) & 0xFFFF
        if mode == "absy":
            low = self.fetch(); high = self.fetch(); return ((low | high << 8) + self.y) & 0xFFFF
        if mode == "indx": return self.read_word_zp((self.fetch() + self.x) & 0xFF)
        if mode == "indy": return (self.read_word_zp(self.fetch()) + self.y) & 0xFFFF
        if mode == "ind":
            low = self.fetch(); high = self.fetch(); pointer = low | high << 8
            # Preserve the original NMOS 6502 page-wrap behavior.
            target_low = self.memory[pointer]
            target_high = self.memory[(pointer & 0xFF00) | ((pointer + 1) & 0x00FF)]
            return target_low | target_high << 8
        raise CpuError(f"unsupported addressing mode: {mode}")

    def compare(self, left: int, right: int) -> None:
        result = left - right
        self.set_flag(FLAG_C, result >= 0)
        self.set_nz(result)

    def adc(self, value: int) -> None:
        if self.get_flag(FLAG_D):
            raise CpuError("decimal-mode ADC is not implemented")
        carry = self.get_flag(FLAG_C)
        result = self.a + value + carry
        byte = result & 0xFF
        self.set_flag(FLAG_C, result > 0xFF)
        self.set_flag(FLAG_V, bool((~(self.a ^ value) & (self.a ^ byte) & 0x80)))
        self.a = self.set_nz(byte)

    def sbc(self, value: int) -> None:
        if self.get_flag(FLAG_D):
            raise CpuError("decimal-mode SBC is not implemented")
        carry = self.get_flag(FLAG_C)
        result = self.a - value - (1 - carry)
        byte = result & 0xFF
        self.set_flag(FLAG_C, result >= 0)
        self.set_flag(FLAG_V, bool(((self.a ^ byte) & (self.a ^ value) & 0x80)))
        self.a = self.set_nz(byte)

    def branch(self, condition: bool) -> None:
        displacement = self.fetch()
        if condition:
            if displacement & 0x80:
                displacement -= 0x100
            self.pc = (self.pc + displacement) & 0xFFFF

    def step(self) -> None:
        instruction_address = self.pc
        opcode = self.fetch()
        instruction = OPCODES[opcode]
        mnemonic = instruction.mnemonic
        mode = instruction.mode
        if mnemonic == "???":
            raise CpuError(f"undocumented opcode ${opcode:02X} at ${instruction_address:04X}")

        self.steps += 1

        if mnemonic in ("BCC", "BCS", "BEQ", "BMI", "BNE", "BPL", "BVC", "BVS"):
            conditions = {
                "BCC": not self.get_flag(FLAG_C), "BCS": self.get_flag(FLAG_C),
                "BEQ": self.get_flag(FLAG_Z), "BMI": self.get_flag(FLAG_N),
                "BNE": not self.get_flag(FLAG_Z), "BPL": not self.get_flag(FLAG_N),
                "BVC": not self.get_flag(FLAG_V), "BVS": self.get_flag(FLAG_V),
            }
            self.branch(bool(conditions[mnemonic]))
            return

        if mnemonic == "BRK":
            raise CpuError(f"BRK reached at ${instruction_address:04X}")
        if mnemonic == "JMP": self.pc = self.address(mode); return
        if mnemonic == "JSR":
            target = self.address(mode); return_address = (self.pc - 1) & 0xFFFF
            self.push(return_address >> 8); self.push(return_address & 0xFF); self.pc = target; return
        if mnemonic == "RTS":
            low = self.pop(); high = self.pop(); self.pc = ((low | high << 8) + 1) & 0xFFFF; return
        if mnemonic == "RTI":
            self.p = (self.pop() & ~FLAG_B) | FLAG_U
            low = self.pop(); high = self.pop(); self.pc = low | high << 8; return

        if mnemonic == "CLC": self.set_flag(FLAG_C, False); return
        if mnemonic == "CLD": self.set_flag(FLAG_D, False); return
        if mnemonic == "CLI": self.set_flag(FLAG_I, False); return
        if mnemonic == "CLV": self.set_flag(FLAG_V, False); return
        if mnemonic == "SEC": self.set_flag(FLAG_C, True); return
        if mnemonic == "SED": self.set_flag(FLAG_D, True); return
        if mnemonic == "SEI": self.set_flag(FLAG_I, True); return
        if mnemonic == "NOP": return

        if mnemonic == "PHA": self.push(self.a); return
        if mnemonic == "PHP": self.push(self.p | FLAG_B | FLAG_U); return
        if mnemonic == "PLA": self.a = self.set_nz(self.pop()); return
        if mnemonic == "PLP": self.p = (self.pop() & ~FLAG_B) | FLAG_U; return

        if mnemonic == "TAX": self.x = self.set_nz(self.a); return
        if mnemonic == "TAY": self.y = self.set_nz(self.a); return
        if mnemonic == "TSX": self.x = self.set_nz(self.sp); return
        if mnemonic == "TXA": self.a = self.set_nz(self.x); return
        if mnemonic == "TXS": self.sp = self.x; return
        if mnemonic == "TYA": self.a = self.set_nz(self.y); return

        if mnemonic == "DEX": self.x = self.set_nz(self.x - 1); return
        if mnemonic == "DEY": self.y = self.set_nz(self.y - 1); return
        if mnemonic == "INX": self.x = self.set_nz(self.x + 1); return
        if mnemonic == "INY": self.y = self.set_nz(self.y + 1); return

        if mnemonic in ("LDA", "LDX", "LDY"):
            value = self.memory[self.address(mode)]
            if mnemonic == "LDA": self.a = self.set_nz(value)
            elif mnemonic == "LDX": self.x = self.set_nz(value)
            else: self.y = self.set_nz(value)
            return

        if mnemonic in ("STA", "STX", "STY"):
            address = self.address(mode)
            self.memory[address] = {"STA": self.a, "STX": self.x, "STY": self.y}[mnemonic]
            return

        if mnemonic in ("ORA", "AND", "EOR", "ADC", "SBC", "CMP", "CPX", "CPY", "BIT"):
            value = self.memory[self.address(mode)]
            if mnemonic == "ORA": self.a = self.set_nz(self.a | value)
            elif mnemonic == "AND": self.a = self.set_nz(self.a & value)
            elif mnemonic == "EOR": self.a = self.set_nz(self.a ^ value)
            elif mnemonic == "ADC": self.adc(value)
            elif mnemonic == "SBC": self.sbc(value)
            elif mnemonic == "CMP": self.compare(self.a, value)
            elif mnemonic == "CPX": self.compare(self.x, value)
            elif mnemonic == "CPY": self.compare(self.y, value)
            else:
                self.set_flag(FLAG_Z, (self.a & value) == 0)
                self.set_flag(FLAG_N, bool(value & 0x80))
                self.set_flag(FLAG_V, bool(value & 0x40))
            return

        if mnemonic in ("INC", "DEC"):
            address = self.address(mode)
            delta = 1 if mnemonic == "INC" else -1
            self.memory[address] = self.set_nz(self.memory[address] + delta)
            return

        if mnemonic == "DCP":
            address = self.address(mode)
            self.memory[address] = (self.memory[address] - 1) & 0xFF
            self.compare(self.a, self.memory[address])
            return

        if mnemonic in ("ASL", "LSR", "ROL", "ROR"):
            accumulator = mode == "acc"
            address = None if accumulator else self.address(mode)
            value = self.a if accumulator else self.memory[address]
            old_carry = self.get_flag(FLAG_C)
            if mnemonic == "ASL":
                self.set_flag(FLAG_C, bool(value & 0x80)); result = (value << 1) & 0xFF
            elif mnemonic == "LSR":
                self.set_flag(FLAG_C, bool(value & 0x01)); result = value >> 1
            elif mnemonic == "ROL":
                self.set_flag(FLAG_C, bool(value & 0x80)); result = ((value << 1) | old_carry) & 0xFF
            else:
                self.set_flag(FLAG_C, bool(value & 0x01)); result = ((old_carry << 7) | (value >> 1)) & 0xFF
            result = self.set_nz(result)
            if accumulator: self.a = result
            else: self.memory[address] = result
            return

        raise CpuError(f"unimplemented {mnemonic}/{mode} at ${instruction_address:04X}")

    def run_until(self, stop_pc: int, max_steps: int = 20_000_000) -> int:
        while self.pc != stop_pc:
            if self.steps >= max_steps:
                raise CpuError(f"step limit reached before ${stop_pc:04X}; PC=${self.pc:04X}")
            self.step()
        return self.steps
