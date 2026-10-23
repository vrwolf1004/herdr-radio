import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
os.environ.setdefault("HERDR_RADIO_LANG", "en")

import radio  # noqa: E402

LOCALES = SRC / "locales"
PLACEHOLDER = re.compile(r"{(\w+)}")


class SearchErrorTest(unittest.TestCase):
    """검색 실패: 화면에는 짧은 문구만, 예외 원문은 host.log 에 한 줄."""

    def setUp(self):
        self.state = tempfile.TemporaryDirectory()
        self.addCleanup(self.state.cleanup)
        patch = mock.patch.dict(os.environ, {"HERDR_PLUGIN_STATE_DIR": self.state.name})
        patch.start()
        self.addCleanup(patch.stop)

    def test_screen_message_hides_the_raw_exception_text(self):
        with mock.patch.object(radio.urllib.request, "urlopen", side_effect=OSError("secret-raw-detail")):
            with self.assertRaises(RuntimeError) as caught:
                radio.api_get("/json/stations/search", {"name": "jazz"})
        self.assertNotIn("secret-raw-detail", str(caught.exception))

    def test_raw_exception_text_is_written_to_host_log_once(self):
        with mock.patch.object(radio.urllib.request, "urlopen", side_effect=OSError("secret-raw-detail")):
            with self.assertRaises(RuntimeError):
                radio.api_get("/json/stations/search", {"name": "jazz"})
        lines = Path(self.state.name, "host.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("secret-raw-detail", lines[0])

    def test_log_write_failure_does_not_hide_the_search_error(self):
        with mock.patch.object(radio.urllib.request, "urlopen", side_effect=OSError("boom")), \
                mock.patch.object(radio.os, "makedirs", side_effect=OSError("disk full")):
            with self.assertRaises(RuntimeError):
                radio.api_get("/json/stations/search", {"name": "jazz"})


class LocaleKeyParityTest(unittest.TestCase):
    def load(self, name):
        return json.loads((LOCALES / f"{name}.json").read_text(encoding="utf-8"))

    def test_every_language_has_the_same_keys_and_placeholders(self):
        base = self.load("en")
        for path in sorted(LOCALES.glob("*.json")):
            messages = self.load(path.stem)
            with self.subTest(language=path.stem):
                self.assertEqual(set(messages), set(base))
                for key, text in base.items():
                    self.assertEqual(set(PLACEHOLDER.findall(messages[key])), set(PLACEHOLDER.findall(text)), key)


if __name__ == "__main__":
    unittest.main()
