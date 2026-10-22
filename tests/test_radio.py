import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
os.environ.setdefault("HERDR_RADIO_LANG", "en")

import radio  # noqa: E402


class PaneAliveTest(unittest.TestCase):
    def test_missing_pane_is_not_alive(self):
        from unittest import mock
        with mock.patch.object(radio.herdr_api, "cli", return_value=None):
            self.assertFalse(radio.pane_alive("wN:p1"))

    def test_existing_pane_is_alive(self):
        from unittest import mock
        with mock.patch.object(radio.herdr_api, "cli", return_value={"pane": {"pane_id": "wN:p1"}}):
            self.assertTrue(radio.pane_alive("wN:p1"))

    def test_no_pane_id_is_not_alive(self):
        self.assertFalse(radio.pane_alive(None))


class ShortNameTest(unittest.TestCase):
    def test_long_name_is_cut_with_ellipsis(self):
        name = "x" * 40
        shortened = radio.short_name(name)
        self.assertEqual(len(shortened), radio.NAME_WIDTH)
        self.assertTrue(shortened.endswith("…"))

    def test_short_name_is_kept_and_blank_becomes_question_mark(self):
        self.assertEqual(radio.short_name("Jazz"), "Jazz")
        self.assertEqual(radio.short_name("   "), "?")


class StationsTest(unittest.TestCase):
    def test_skips_empty_url_and_uses_url_as_name_when_missing(self):
        items = [{"url": "https://a"}, {"name": "B", "url": ""}, {"name": "C", "url": " https://c "}, "junk"]
        stations = radio.clean_stations(items)
        self.assertEqual(stations, [
            {"name": "https://a", "url": "https://a", "country": ""},
            {"name": "C", "url": "https://c", "country": ""},
        ])

    def test_non_list_stations_gives_empty(self):
        with mock.patch.object(radio, "read_config", return_value={"stations": {"url": "x"}}):
            self.assertEqual(radio.load_stations(), [])


class SearchResponseTest(unittest.TestCase):
    def test_empty_url_resolved_falls_back_to_url(self):
        response = [
            {"name": " Jazz ", "country": "KR", "url_resolved": "", "url": "https://j"},
            {"name": "No URL", "url_resolved": "", "url": ""},
            {"name": "Rock", "url_resolved": "https://r", "url": "https://old"},
        ]
        with mock.patch.object(radio, "api_get", return_value=response):
            results = radio.search("x")
        self.assertEqual(results, [
            {"name": "Jazz", "country": "KR", "url": "https://j"},
            {"name": "Rock", "country": "", "url": "https://r"},
        ])


class PlayerPatternTest(unittest.TestCase):
    def matches(self, command_line):
        return any(re.search(pattern, command_line) for pattern in radio.PLAYER_PATTERNS)

    def test_player_command_lines_match(self):
        self.assertTrue(self.matches("/usr/bin/mpv --no-video --title=herdr-radio https://x"))
        self.assertTrue(self.matches("ffplay -nodisp -window_title herdr-radio https://x"))

    def test_host_command_line_does_not_match(self):
        host = "python3 -X utf8 /home/u/.local/share/herdr-radio/src/radio.py host --state /x/herdr/plugins/herdr-radio"
        self.assertFalse(self.matches(host))

    def test_other_player_without_marker_does_not_match(self):
        self.assertFalse(self.matches("mpv https://some-stream"))


class QueryTimeoutTest(unittest.TestCase):
    def test_timeout_returns_empty_output(self):
        with mock.patch.object(radio.subprocess, "run",
                               side_effect=subprocess.TimeoutExpired(cmd="pgrep", timeout=5)):
            self.assertEqual(radio._query(["pgrep", "-f", "x"]), "")

    def test_timeout_is_passed_to_subprocess(self):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="42\n", stderr="")
        with mock.patch.object(radio.subprocess, "run", return_value=completed) as run:
            self.assertEqual(radio._query(["pgrep", "-f", "x"]), "42\n")
        self.assertEqual(run.call_args.kwargs["timeout"], radio.PROCESS_QUERY_SECONDS)


class SearchCacheTest(unittest.TestCase):
    def test_second_search_within_ttl_uses_cache(self):
        results = [{"name": "Jazz", "country": "", "url": "https://j"}]
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(radio, "search", return_value=results) as search:
            first = radio.cached_search(directory, "jazz")
            second = radio.cached_search(directory, "Jazz ")
        self.assertEqual(first, results)
        self.assertEqual(second, results)
        search.assert_called_once()

    def test_expired_entry_is_searched_again(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(radio, "search", return_value=[]) as search:
            radio.cached_search(directory, "jazz")
            cache_path = os.path.join(directory, radio.SEARCH_CACHE_FILE)
            with open(cache_path, encoding="utf-8") as file:
                cache = json.load(file)
            for entry in cache.values():
                entry["at"] -= radio.SEARCH_CACHE_SECONDS + 1
            with open(cache_path, "w", encoding="utf-8") as file:
                json.dump(cache, file)
            radio.cached_search(directory, "jazz")
        self.assertEqual(search.call_count, 2)


if __name__ == "__main__":
    unittest.main()
