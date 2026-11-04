from __future__ import annotations

import json
import asyncio
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace

from bt_sentinel.scanner import scan_ble
from bt_sentinel.core import (
    advertisement_to_record,
    append_audit_event,
    load_inventory,
    merge_inventory,
    merge_record,
    normalize_address,
    parse_classic_device_line,
    render_html_report,
    save_json_atomic,
    signal_label,
)


class CoreTests(unittest.TestCase):
    def test_mac_is_normalized(self):
        self.assertEqual(normalize_address("aa:bb:cc:dd:ee:ff"), "AA:BB:CC:DD:EE:FF")

    def test_opaque_windows_ble_identifier_is_allowed(self):
        value = "BluetoothLE#BluetoothLE00:11:22:33:44:55-00:00"
        self.assertEqual(normalize_address(value), value)

    def test_empty_identifier_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_address("  ")

    def test_signal_labels(self):
        self.assertEqual(signal_label(-45), "Strong")
        self.assertEqual(signal_label(-65), "Medium")
        self.assertEqual(signal_label(-85), "Weak")
        self.assertEqual(signal_label(None), "N/A")
        self.assertEqual(signal_label("unknown"), "N/A")

    def test_advertisement_is_serializable(self):
        device = SimpleNamespace(address="aa:bb:cc:dd:ee:ff", name="Sensor")
        advertisement = SimpleNamespace(
            service_uuids=["180D"], manufacturer_data={76: b"\\x01\\x02"},
            rssi=-61, tx_power=4, local_name="Local Sensor",
        )
        record = advertisement_to_record(device, advertisement)
        self.assertEqual(record["address"], "AA:BB:CC:DD:EE:FF")
        self.assertEqual(record["name"], "Sensor")
        self.assertEqual(record["signal"], "Medium")
        json.dumps(record)

    def test_merge_keeps_first_seen_and_increments_count(self):
        original = {
            "address": "AA:BB:CC:DD:EE:FF", "name": "Unknown", "transport": "BLE",
            "rssi": -80, "service_uuids": ["180D"], "manufacturer_data": {},
            "first_seen": "2026-01-01T00:00:00+00:00", "last_seen": "2026-01-01T00:00:00+00:00", "seen_count": 1,
        }
        update = {
            "address": "AA:BB:CC:DD:EE:FF", "name": "Heart Sensor", "transport": "BLE",
            "rssi": -60, "service_uuids": ["180F"], "manufacturer_data": {"76": "0102"},
            "first_seen": "2026-01-02T00:00:00+00:00", "last_seen": "2026-01-02T00:00:00+00:00", "seen_count": 1,
        }
        merged = merge_record(original, update)
        self.assertEqual(merged["name"], "Heart Sensor")
        self.assertEqual(merged["first_seen"], original["first_seen"])
        self.assertEqual(merged["seen_count"], 2)
        self.assertEqual(set(merged["service_uuids"]), {"180D", "180F"})
        self.assertEqual(merged["rssi"], -60)

    def test_ble_scanner_explicitly_uses_passive_mode(self):
        captured = {}

        class FakeScanner:
            def __init__(self, detection_callback=None, scanning_mode=None):
                captured["scanning_mode"] = scanning_mode
                self.callback = detection_callback

            async def start(self):
                device = SimpleNamespace(address="AA:BB:CC:DD:EE:FF", name="Lab sensor")
                advertisement = SimpleNamespace(
                    service_uuids=[], manufacturer_data={}, rssi=-58, tx_power=None, local_name=None
                )
                self.callback(device, advertisement)

            async def stop(self):
                captured["stopped"] = True

        fake_module = SimpleNamespace(BleakScanner=FakeScanner)
        observed = []
        with patch("bt_sentinel.scanner.platform.system", return_value="Windows"):
            with patch.dict(sys.modules, {"bleak": fake_module}):
                count, error = asyncio.run(scan_ble(0, observed.append))

        self.assertEqual(captured["scanning_mode"], "passive")
        self.assertTrue(captured["stopped"])
        self.assertEqual(count, 1)
        self.assertIsNone(error)
        self.assertEqual(observed[0]["address"], "AA:BB:CC:DD:EE:FF")

    def test_ble_scanner_skips_macos_to_preserve_passive_mode(self):
        with patch("bt_sentinel.scanner.platform.system", return_value="Darwin"):
            count, error = asyncio.run(scan_ble(1, lambda _record: None))
        self.assertEqual(count, 0)
        self.assertIn("not supported on macOS", error)

    def test_parse_classic_device_line(self):
        record = parse_classic_device_line("[NEW] Device aa:bb:cc:dd:ee:ff Test Headphones")
        self.assertIsNotNone(record)
        self.assertEqual(record["address"], "AA:BB:CC:DD:EE:FF")
        self.assertEqual(record["name"], "Test Headphones")
        self.assertIsNone(parse_classic_device_line("No Bluetooth device in line"))
        rssi_update = parse_classic_device_line("[CHG] Device AA:BB:CC:DD:EE:FF RSSI: -62")
        self.assertEqual(rssi_update["name"], "Unknown")
        name_update = parse_classic_device_line("[CHG] Device AA:BB:CC:DD:EE:FF Name: Headphones")
        self.assertEqual(name_update["name"], "Headphones")

    def test_inventory_merge(self):
        old = [{"address": "AA:BB:CC:DD:EE:FF", "name": "Unknown", "transport": "BLE", "service_uuids": [], "manufacturer_data": {}, "seen_count": 1}]
        new = [{"address": "AA:BB:CC:DD:EE:FF", "name": "Lab tag", "transport": "BLE", "service_uuids": ["180F"], "manufacturer_data": {}, "seen_count": 1}]
        result = merge_inventory(old, new)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Lab tag")
        self.assertEqual(result[0]["seen_count"], 2)

    def test_audit_event_is_json_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "logs" / "audit.jsonl"
            append_audit_event(path, "TEST_EVENT", {"count": 3})
            record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["event"], "TEST_EVENT")
            self.assertEqual(record["details"]["count"], 3)
            self.assertIn("timestamp", record)

    def test_atomic_inventory_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "inventory.json"
            save_json_atomic(path, [{"address": "AA:BB:CC:DD:EE:FF"}])
            self.assertEqual(load_inventory(path)[0]["address"], "AA:BB:CC:DD:EE:FF")

    def test_report_escapes_untrusted_values_and_has_no_cve_guess(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            device = {"address": "AA:BB:CC:DD:EE:FF", "name": "<script>alert(1)</script>",
                      "transport": "BLE", "service_uuids": [], "manufacturer_data": {}}
            render_html_report([device], {}, output)
            html = output.read_text(encoding="utf-8")
            self.assertNotIn("<script>alert(1)</script>", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertIn("Não executa exploits", html)
            self.assertNotIn("CVE-", html)


if __name__ == "__main__":
    unittest.main()
