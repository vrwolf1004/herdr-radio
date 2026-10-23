import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import radio  # noqa: E402

MANIFEST = Path(__file__).resolve().parents[1] / "herdr-plugin.toml"


def manifest_version():
    # Python 3.8 에서도 돌도록 tomllib 대신 version 줄만 읽는다.
    match = re.search(r'^version\s*=\s*"([^"]+)"', MANIFEST.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else None


class UserAgentTest(unittest.TestCase):
    def test_plugin_version_matches_the_manifest(self):
        self.assertEqual(radio.PLUGIN_VERSION, manifest_version())

    def test_user_agent_carries_the_manifest_version(self):
        self.assertEqual(radio.USER_AGENT, f"herdr-radio/{manifest_version()}")


if __name__ == "__main__":
    unittest.main()
