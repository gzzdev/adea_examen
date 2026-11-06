import unittest

from app.parsing.clave_elector import extract


class ClaveElectorParsingTests(unittest.TestCase):
    def test_extracts_value_after_label(self):
        self.assertEqual(extract(["CLAVE DE ELECTOR ABCDEF01020304H123"]),
                         "ABCDEF01020304H123")

    def test_rejects_incomplete_value(self):
        self.assertIsNone(extract(["ABCDEF01020304H12"]))


if __name__ == "__main__":
    unittest.main()
