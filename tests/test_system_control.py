from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bt_sentinel import system_control


class SystemControlTests(unittest.TestCase):
    def test_youtube_http_is_rejected(self):
        success, message = system_control.open_media_source("http://youtube.com/watch?v=abc")
        self.assertFalse(success)
        self.assertIn("HTTPS", message)

    def test_non_youtube_https_is_rejected(self):
        success, message = system_control.open_media_source("https://example.com/audio.mp3")
        self.assertFalse(success)
        self.assertIn("YouTube", message)

    def test_missing_audio_file_is_rejected(self):
        success, message = system_control.open_media_source("Z:/not/a/real/file.mp3")
        self.assertFalse(success)
        self.assertIn("não encontrado", message)

    def test_invalid_media_action_is_rejected(self):
        success, message = system_control.control_media("pair_by_mac")
        self.assertFalse(success)
        self.assertIn("inválido", message)

    def test_linux_playerctl_play_pause_uses_local_media_session(self):
        fake_result = type("Result", (), {"returncode": 0, "stderr": ""})()
        with patch("bt_sentinel.system_control.platform.system", return_value="Linux"):
            with patch("bt_sentinel.system_control.shutil.which", return_value="/usr/bin/playerctl"):
                with patch("bt_sentinel.system_control.subprocess.run", return_value=fake_result) as run:
                    success, message = system_control.control_media("play_pause")
        self.assertTrue(success)
        self.assertIn("sessão ativa", message)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ["/usr/bin/playerctl", "play-pause"])


if __name__ == "__main__":
    unittest.main()
