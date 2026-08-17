import tempfile
import unittest
from pathlib import Path

from logic import ClipboardHistoryManager, SettingsManager


class SettingsManagerTests(unittest.TestCase):
    def test_default_settings_are_loaded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            manager = SettingsManager(settings_path=path)
            settings = manager.load_settings()

            self.assertIn("max_history", settings)
            self.assertIn("poll_interval_ms", settings)
            self.assertIn("always_on_top", settings)
            self.assertTrue(settings["max_history"] > 0)

    def test_settings_can_be_saved_and_reloaded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            manager = SettingsManager(settings_path=path)
            manager.save_settings({
                "max_history": 42,
                "poll_interval_ms": 750,
                "always_on_top": True,
            })

            reloaded = manager.load_settings()
            self.assertEqual(reloaded["max_history"], 42)
            self.assertEqual(reloaded["poll_interval_ms"], 750)
            self.assertTrue(reloaded["always_on_top"])

    def test_partial_settings_update_preserves_existing_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            manager = SettingsManager(settings_path=path)
            manager.save_settings({
                "max_history": 42,
                "poll_interval_ms": 750,
                "always_on_top": False,
            })

            updated = manager.save_settings({"always_on_top": True})

            self.assertEqual(updated["max_history"], 42)
            self.assertEqual(updated["poll_interval_ms"], 750)
            self.assertTrue(updated["always_on_top"])


class ClipboardHistoryManagerTests(unittest.TestCase):
    def test_setting_max_items_trims_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "clipboard_history.json"
            manager = ClipboardHistoryManager(max_items=3, storage_path=path)
            manager.add_item("first")
            manager.add_item("second")
            manager.add_item("third")
            manager.add_item("fourth")

            self.assertEqual(len(manager.get_history()), 3)

            manager.set_max_items(2)
            self.assertEqual(len(manager.get_history()), 2)
            self.assertEqual(manager.get_history()[0].text, "fourth")


if __name__ == "__main__":
    unittest.main()
