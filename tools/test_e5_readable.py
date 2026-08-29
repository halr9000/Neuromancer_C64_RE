#!/usr/bin/env python3

from __future__ import annotations

import unittest

from tools.extract_e5_readable import PetsciiTerminal, clean_solution_replay


class PetsciiTerminalTests(unittest.TestCase):
    def test_logical_line_wrap_and_return(self) -> None:
        terminal = PetsciiTerminal()
        for char in "A" * 40:
            terminal.put(char)
        self.assertEqual((terminal.row, terminal.offset), (1, 40))
        terminal.carriage_return()
        terminal.put("B")
        self.assertEqual("".join(terminal.screen[0]), "A" * 40)
        self.assertEqual(terminal.screen[2][0], "B")

    def test_delete_shifts_left(self) -> None:
        terminal = PetsciiTerminal()
        for char in "ABCD":
            terminal.put(char)
        terminal.move_left()
        terminal.move_left()
        terminal.delete()
        self.assertEqual("".join(terminal.screen[0][:4]), "ACD ")

    def test_insert_shifts_right(self) -> None:
        terminal = PetsciiTerminal()
        for char in "ABCD":
            terminal.put(char)
        terminal.move_left()
        terminal.move_left()
        terminal.insert()
        terminal.put("X")
        self.assertEqual("".join(terminal.screen[0][:5]), "ABXCD")

    def test_editorial_repairs_are_explicit(self) -> None:
        # Exercise the strict replacement contract against the actual replay
        # fragments, without making this unit test depend on generated files.
        replay = """===== SOLUTION SECTION 01 =====
       --------------------
      ---    NEUROMANC--   -
      ------    SOL-----   -
      ------------------   -
      -  BY THE ANNIHILATOR-
      ---    MAY 2, 19-- -
      -------------------
ON THE PANTHER MODERNS DB FOR THE LINK
ND THEN USE COPTALK TO TALK
USEFUL NUMBERS

YOUR BAMA ID NUMBER...      056306118
LARRY MOE'S ID NUMBER.   062788138
ACCOUNT AT GEMEINSCHAFT.       646328356
481   ACCOUNT AT BOZOB.........   712345
ACCOUNT AT BACK OF BER.........328356481
1200                    ....
AUTHORIZATION CODE .........RNE..
VAULT CODE FOR GEMEINSCHA...FT...
DIXIE FLATLINE'S N/.........LYMA1211MARZ
TOSHIRO'S NUMBER..................BG1066
ROMBO'S NUMBER...................0467839
                              ...6905984
                              ...5521426
===== SOLUTION SECTION 07 =====
ELOW IS THE LOCATIONS ON WHERE
===== SOLUTION SECTION 11 =====
 HOPE THAT THIS HELP FILE I
SPECIAL HELLOS TO IRON FIST.



           THE ANNIHILATOR"""
        cleaned, repairs = clean_solution_replay(replay)
        self.assertIn("ACCOUNT AT BOZOBANK...............712345450134", cleaned)
        self.assertIn("BELOW IS THE LOCATIONS", cleaned)
        self.assertEqual(len(repairs), 6)


if __name__ == "__main__":
    unittest.main()
