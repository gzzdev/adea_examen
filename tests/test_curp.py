import unittest

from app.parsing.curp import extract, is_valid


class CurpParsingTests(unittest.TestCase):
    def test_accepts_valid_synthetic_curp(self):
        value = "BOXW310820HNERXN09"
        self.assertTrue(is_valid(value))
        self.assertEqual(extract([f"CURP {value}"]), value)

    def test_rejects_wrong_check_digit(self):
        self.assertFalse(is_valid("BOXW310820HNERXN08"))


if __name__ == "__main__":
    unittest.main()
