from __future__ import annotations

import asyncio
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rich.console import Console

from bt_sentinel.ui import SentinelApp


class TerminalFlowTests(unittest.TestCase):
    def test_live_discovery_updates_inventory_and_audit_log(self):
        async def fake_discovery(duration, transports, on_device, on_status):
            self.assertEqual(duration, 5)
            self.assertEqual(transports, "ble")
            on_status("Passive BLE listening")
            on_device({
                "address": "AA:BB:CC:DD:EE:FF",
                "name": "Test beacon",
                "transport": "BLE",
                "rssi": -64,
                "signal": "Medium",
                "service_uuids": ["180D"],
                "manufacturer_data": {},
                "first_seen": "2026-11-04T00:00:00+00:00",
                "last_seen": "2026-11-04T00:00:00+00:00",
                "seen_count": 1,
            })
            await asyncio.sleep(0)
            return []

        with tempfile.TemporaryDirectory() as directory:
            app = SentinelApp(Path(directory))
            output = io.StringIO()
            app.console = Console(file=output, force_terminal=False, width=100, color_system=None)
            with patch("bt_sentinel.ui.run_discovery", new=fake_discovery):
                with patch("bt_sentinel.ui.Prompt.ask", return_value=""):
                    found = app.live_discovery(duration=5, transports="ble")

            self.assertEqual(len(found), 1)
            inventory = json.loads((Path(directory) / "data" / "inventory.json").read_text(encoding="utf-8"))
            self.assertEqual(inventory[0]["name"], "Test beacon")
            events = [json.loads(line)["event"] for line in (Path(directory) / "logs" / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(events, ["DISCOVERY_STARTED", "DISCOVERY_FINISHED"])


if __name__ == "__main__":
    unittest.main()
