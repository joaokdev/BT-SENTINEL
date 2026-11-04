from __future__ import annotations

import unittest

from bt_sentinel.device_intel import classify_device


class DeviceIntelligenceTests(unittest.TestCase):
    def test_headphones_are_classified_from_name(self):
        profile = classify_device({"name": "Sony WH-1000XM5", "service_uuids": []})
        self.assertEqual(profile["category"], "Fone / headset")
        self.assertEqual(profile["confidence"], "Média")

    def test_speaker_is_classified_from_name(self):
        profile = classify_device({"name": "JBL Flip 6", "service_uuids": []})
        self.assertEqual(profile["category"], "Caixa de som")

    def test_audio_service_class_is_not_presented_as_confirmed_device(self):
        profile = classify_device({"name": "Unknown", "service_uuids": ["0000110B-0000-1000-8000-00805F9B34FB"]})
        self.assertEqual(profile["category"], "Áudio Bluetooth")
        self.assertIn("não prova", profile["disclaimer"])

    def test_unknown_stays_unknown(self):
        profile = classify_device({"name": "", "service_uuids": []})
        self.assertEqual(profile["category"], "Dispositivo não identificado")
        self.assertEqual(profile["confidence"], "Baixa")


if __name__ == "__main__":
    unittest.main()
