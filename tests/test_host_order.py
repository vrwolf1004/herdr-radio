import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
os.environ.setdefault("HERDR_RADIO_LANG", "en")

import radio  # noqa: E402

DE, NL, AT = radio.API_HOSTS


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return b"[]"


class FakeNetwork:
    """호스트별로 실패/성공을 정하고, 어떤 호스트를 어떤 순서로 불렀는지 기록한다."""

    def __init__(self, failing):
        self.failing = set(failing)
        self.called = []

    def urlopen(self, req, timeout=None):
        host = req.full_url.split("/")[2]
        self.called.append(host)
        if host in self.failing:
            raise OSError("host down")
        return FakeResponse()


class HostOrderTest(unittest.TestCase):
    def setUp(self):
        self.state = tempfile.TemporaryDirectory()
        self.addCleanup(self.state.cleanup)
        patch = mock.patch.dict(os.environ, {"HERDR_PLUGIN_STATE_DIR": self.state.name})
        patch.start()
        self.addCleanup(patch.stop)
        saved = radio.last_good_host
        radio.last_good_host = None  # 프로그램을 막 켠 상태에서 시작한다
        self.addCleanup(setattr, radio, "last_good_host", saved)

    def search(self, network):
        with mock.patch.object(radio.urllib.request, "urlopen", side_effect=network.urlopen):
            return radio.api_get("/json/stations/search", {"name": "jazz"})

    def test_first_request_uses_the_default_order_and_falls_through_to_a_working_host(self):
        network = FakeNetwork(failing=[DE])
        self.search(network)
        self.assertEqual(network.called, [DE, NL])

    def test_next_request_tries_the_last_working_host_first(self):
        network = FakeNetwork(failing=[DE])
        self.search(network)
        network.called.clear()
        self.search(network)
        self.assertEqual(network.called, [NL])  # NL 이 성공하면 바로 끝난다

    def test_failed_preferred_host_falls_back_to_the_rest_in_default_order(self):
        network = FakeNetwork(failing=[DE])
        self.search(network)  # NL 이 마지막 성공
        network.failing = {NL}
        network.called.clear()
        self.search(network)
        self.assertEqual(network.called, [NL, DE])  # 나머지는 기존 순서로 보고, DE 가 응답하면 AT 는 부르지 않는다

    def test_all_hosts_failing_gives_the_same_short_error_and_host_log_line(self):
        network = FakeNetwork(failing=radio.API_HOSTS)
        with self.assertRaises(RuntimeError) as caught:
            self.search(network)
        self.assertEqual(network.called, [DE, NL, AT])
        self.assertEqual(str(caught.exception), radio.i18n.t("error.radio_browser"))
        lines = Path(self.state.name, "host.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("host down", lines[0])

    def test_after_total_failure_the_default_order_is_kept(self):
        network = FakeNetwork(failing=radio.API_HOSTS)
        with self.assertRaises(RuntimeError):
            self.search(network)
        network.failing = set()
        network.called.clear()
        self.search(network)
        self.assertEqual(network.called, [DE])

    def test_restart_forgets_the_preferred_host(self):
        network = FakeNetwork(failing=[DE])
        self.search(network)
        radio.last_good_host = None  # 프로그램을 다시 켠 것과 같다
        network.called.clear()
        self.search(network)
        self.assertEqual(network.called, [DE, NL])

    def test_host_order_puts_the_remembered_host_first_without_duplicates(self):
        radio.last_good_host = AT
        self.assertEqual(radio.host_order(), [AT, DE, NL])
        radio.last_good_host = "unknown.example"
        self.assertEqual(radio.host_order(), list(radio.API_HOSTS))


if __name__ == "__main__":
    unittest.main()
