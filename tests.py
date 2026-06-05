import unittest
import os
from utils import safe_relative_path, safe_path, SERVE_DIRECTORY
from translations import TRANSLATIONS

class TestMSXServer(unittest.TestCase):
    def test_safe_relative_path(self):
        # Good paths
        self.assertEqual(safe_relative_path("test/file.txt"), "test/file.txt")
        self.assertEqual(safe_relative_path(""), "")
        
        # Dangerous paths should raise ValueError
        with self.assertRaises(ValueError):
            safe_relative_path("../outside.txt")
        with self.assertRaises(ValueError):
            safe_relative_path("/absolute/path")

    def test_safe_path(self):
        # Should stay within SERVE_DIRECTORY
        path = safe_path("subdir/game.rom")
        self.assertTrue(path.startswith(os.path.abspath(SERVE_DIRECTORY)))

    def test_translations(self):
        # Verify both languages exist and have same keys
        self.assertIn("nl", TRANSLATIONS)
        self.assertIn("en", TRANSLATIONS)
        nl_keys = set(TRANSLATIONS["nl"].keys())
        en_keys = set(TRANSLATIONS["en"].keys())
        self.assertEqual(nl_keys, en_keys, "NL and EN translation keys must match!")

if __name__ == "__main__":
    unittest.main()
