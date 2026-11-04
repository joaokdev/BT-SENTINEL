from __future__ import annotations

import re
from typing import Any


# Heuristics only: advertisements and names are not authoritative device identities.
_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Fone / headset", ("headphone", "headset", "earbud", "earphone", "airpods", "galaxy buds", "buds", "freebuds", "fone", "auricular", "earbuds", "wh 1000", "wf 1000", "quietcomfort", "qc 35", "qc 45", "qc ultra")),
    ("Caixa de som", ("speaker", "soundbar", "soundlink", "flip", "charge", "boombox", "caixa de som", "alto-falante")),
    ("Dispositivo de áudio", ("jbl", "bose", "soundcore", "beats", "anker", "sony")),
    ("Smartphone", ("iphone", "pixel", "galaxy s", "galaxy note", "redmi", "xiaomi", "motorola", "moto g", "oneplus", "huawei p", "smartphone", "phone")),
    ("Smartwatch / wearable", ("watch", "smartwatch", "band", "fitbit", "garmin", "mi band", "amazfit", "wearable")),
    ("Computador", ("macbook", "laptop", "notebook", "thinkpad", "desktop", "windows pc", "imac", "computer", "pc-")),
    ("TV / multimídia", ("smart tv", "android tv", "google tv", "fire tv", "roku", "chromecast", "tv box")),
    ("Controle / gamepad", ("controller", "gamepad", "dualsense", "dualshock", "xbox", "joy-con", "gamepad")),
    ("Teclado / mouse", ("keyboard", "mouse", "trackpad", "teclado", "logitech k", "mx master")),
    ("Impressora", ("printer", "impressora", "brother", "epson", "canon pixma", "hp deskjet")),
    ("Sensor / IoT", ("sensor", "beacon", "temperature", "thermometer", "heart rate", "smart tag", "tile", "tracker")),
)

# Bluetooth SIG service classes commonly associated with audio/HID profiles.
_AUDIO_UUIDS = {
    "110a", "110b", "110e", "110f", "111e", "111f", "112d", "1134",
    "0000110a", "0000110b", "0000110e", "0000110f", "0000111e", "0000111f",
    "0000112d", "00001134",
}
_HID_UUIDS = {"1812", "1124", "00001124"}
_HEART_UUIDS = {"180d", "0000180d"}
_BATTERY_UUIDS = {"180f", "0000180f"}


def _uuid_short(value: Any) -> str:
    text = str(value).strip().lower().replace("-", "")
    if text.startswith("0000") and len(text) >= 8:
        return text[:8]
    return text


def classify_device(record: dict[str, Any]) -> dict[str, Any]:
    """Return a cautious device-family guess with confidence and visible evidence."""
    name = str(record.get("name") or "").strip()
    normalized = re.sub(r"[^a-z0-9]+", " ", name.casefold()).strip()
    service_values = {_uuid_short(value) for value in (record.get("service_uuids") or [])}
    evidence: list[str] = []

    for category, keywords in _PATTERNS:
        matched = next((word for word in keywords if word in normalized), None)
        if matched:
            evidence.append(f"Nome contém o indicador '{matched}'.")
            return {"category": category, "confidence": "Média", "evidence": evidence,
                    "disclaimer": "Estimativa por nome anunciado; confirme no sistema ou no próprio aparelho."}

    if service_values & _AUDIO_UUIDS:
        evidence.append("Foram observados UUIDs de classes de serviço Bluetooth relacionadas a áudio.")
        return {"category": "Áudio Bluetooth", "confidence": "Média", "evidence": evidence,
                "disclaimer": "O UUID anunciado não prova que o serviço remoto esteja acessível."}
    if service_values & _HID_UUIDS:
        evidence.append("Foi observado um UUID associado a dispositivos de interface humana (HID).")
        return {"category": "Teclado / mouse / HID", "confidence": "Baixa", "evidence": evidence,
                "disclaimer": "O UUID não distingue sozinho teclado, mouse, controle ou outro HID."}
    if service_values & _HEART_UUIDS:
        evidence.append("Foi observado o serviço padronizado de frequência cardíaca.")
        return {"category": "Sensor de saúde / wearable", "confidence": "Média", "evidence": evidence,
                "disclaimer": "A classificação descreve o serviço anunciado, não a identidade do fabricante."}
    if service_values & _BATTERY_UUIDS:
        evidence.append("Foi observado o serviço padronizado de bateria.")
        return {"category": "Acessório BLE", "confidence": "Baixa", "evidence": evidence,
                "disclaimer": "O serviço de bateria é comum em muitas classes de acessórios."}

    return {"category": "Dispositivo não identificado", "confidence": "Baixa", "evidence": ["Nome e serviços anunciados insuficientes para uma classificação confiável."],
            "disclaimer": "Não é possível inferir a classe do hardware apenas com os dados observados."}
