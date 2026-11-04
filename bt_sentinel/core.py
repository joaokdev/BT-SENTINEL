from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from . import __version__
from .device_intel import classify_device

MAC_RE = re.compile(r"^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
MAC_SEARCH_RE = re.compile(r"(?i)(?:[0-9a-f]{2}:){5}[0-9a-f]{2}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_address(value: str) -> str:
    """Normalize a MAC address while allowing opaque OS-specific BLE IDs."""
    address = str(value).strip()
    if not address:
        raise ValueError("Bluetooth address/identifier is empty")
    if len(address) > 180 or any(ord(ch) < 32 for ch in address):
        raise ValueError("Bluetooth address/identifier is invalid")
    if MAC_RE.fullmatch(address):
        return address.upper()
    return address


def signal_label(rssi: int | None) -> str:
    try:
        rssi = int(rssi) if rssi is not None else None
    except (TypeError, ValueError):
        return "N/A"
    if rssi is None:
        return "N/A"
    if rssi >= -55:
        return "Strong"
    if rssi >= -70:
        return "Medium"
    return "Weak"


def advertisement_to_record(device: Any, advertisement: Any) -> dict[str, Any]:
    address = normalize_address(getattr(device, "address", ""))
    service_uuids = sorted({str(item).lower() for item in (getattr(advertisement, "service_uuids", None) or [])})
    manufacturer_data = {
        str(company_id): bytes(payload).hex()
        for company_id, payload in (getattr(advertisement, "manufacturer_data", None) or {}).items()
    }
    rssi = getattr(advertisement, "rssi", None)
    if rssi is None:
        rssi = getattr(device, "rssi", None)
    now = utc_now()
    return {
        "address": address,
        "name": getattr(device, "name", None) or getattr(advertisement, "local_name", None) or "Unknown",
        "transport": "BLE",
        "rssi": int(rssi) if rssi is not None else None,
        "signal": signal_label(int(rssi)) if rssi is not None else "N/A",
        "service_uuids": service_uuids,
        "manufacturer_data": manufacturer_data,
        "tx_power": getattr(advertisement, "tx_power", None),
        "first_seen": now,
        "last_seen": now,
        "seen_count": 1,
    }


def merge_record(existing: dict[str, Any] | None, incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge observations while preserving first-seen and cumulative sightings."""
    item = dict(existing or {})
    if not item:
        item.update(incoming)
        item.setdefault("seen_count", 1)
        return item

    item["address"] = incoming.get("address", item.get("address", ""))
    new_name = incoming.get("name")
    if new_name and new_name != "Unknown":
        item["name"] = new_name
    elif not item.get("name"):
        item["name"] = "Unknown"

    transports = set(str(item.get("transport", "")).split("+") + str(incoming.get("transport", "")).split("+"))
    item["transport"] = "+".join(sorted(part for part in transports if part))

    for key in ("service_uuids",):
        item[key] = sorted(set(item.get(key, []) or []) | set(incoming.get(key, []) or []))
    for key in ("manufacturer_data",):
        merged_data = dict(item.get(key, {}) or {})
        merged_data.update(incoming.get(key, {}) or {})
        item[key] = merged_data

    if incoming.get("rssi") is not None:
        item["rssi"] = incoming["rssi"]
        item["signal"] = signal_label(incoming["rssi"])
    if incoming.get("tx_power") is not None:
        item["tx_power"] = incoming["tx_power"]

    item["first_seen"] = item.get("first_seen") or incoming.get("first_seen") or utc_now()
    item["last_seen"] = incoming.get("last_seen") or utc_now()
    try:
        previous_count = max(0, int(item.get("seen_count", 0)))
    except (TypeError, ValueError):
        previous_count = 0
    try:
        incoming_count = max(1, int(incoming.get("seen_count", 1)))
    except (TypeError, ValueError):
        incoming_count = 1
    item["seen_count"] = previous_count + incoming_count
    return item


def merge_inventory(existing: list[dict[str, Any]], observed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for record in existing + observed:
        address = normalize_address(record.get("address", ""))
        merged[address] = merge_record(merged.get(address), record)
    return sorted(merged.values(), key=lambda record: (str(record.get("name", "")).casefold(), record["address"]))


def load_inventory(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read inventory file {path}: {exc}") from exc
    if not isinstance(payload, list):
        raise ValueError("Inventory format must be a JSON array")
    for item in payload:
        if not isinstance(item, dict) or not item.get("address"):
            raise ValueError("Inventory contains an invalid device record")
    return payload


def append_audit_event(path: Path, event: str, details: dict[str, Any] | None = None) -> Path:
    """Append one structured local audit event without collecting device payloads."""
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": utc_now(),
        "event": str(event)[:80],
        "details": details or {},
    }
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        stream.write("\n")
    return path


def save_json_atomic(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, ensure_ascii=False)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(serialized)
            stream.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
    return path


def parse_classic_device_line(line: str) -> dict[str, Any] | None:
    match = MAC_SEARCH_RE.search(line)
    if not match:
        return None
    address = match.group(0).upper()
    name_match = re.search(r"\bDevice\s+" + re.escape(match.group(0)) + r"\s+(.+)$", line, re.IGNORECASE)
    suffix = name_match.group(1).strip() if name_match else ""
    if suffix.lower().startswith("name:"):
        name = suffix.split(":", 1)[1].strip() or "Unknown"
    elif suffix and not re.match(r"(?i)^(rssi|uuid|paired|trusted|blocked|connected|services|icon|legacy-pairing|txpower|modalias|manufacturerdata|service-resolved|discoverable|pairable):", suffix):
        name = suffix if not line.lstrip().startswith("[CHG]") else "Unknown"
    else:
        name = "Unknown"
    now = utc_now()
    return {
        "address": address,
        "name": name or "Unknown",
        "transport": "BlueZ",
        "rssi": None,
        "signal": "N/A",
        "service_uuids": [],
        "manufacturer_data": {},
        "tx_power": None,
        "first_seen": now,
        "last_seen": now,
        "seen_count": 1,
    }


def render_html_report(devices: list[dict[str, Any]], adapter: dict[str, Any], output: Path) -> Path:
    """Create a self-contained HTML report; all observed values are escaped."""
    output.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(adapter, dict):
        adapter = {}
    rows: list[str] = []
    for record in devices:
        services = ", ".join(str(value) for value in (record.get("service_uuids", []) or [])) or "—"
        manufacturer_data = record.get("manufacturer_data") or {}
        manufacturer = ", ".join(str(value) for value in manufacturer_data.keys()) if isinstance(manufacturer_data, dict) else "—"
        manufacturer = manufacturer or "—"
        profile = classify_device(record)
        rows.append(
            "<tr>"
            f"<td>{escape(str(record.get('name', 'Unknown')))}</td>"
            f"<td>{escape(profile['category'])} <span class=\"muted\">({escape(profile['confidence'].lower())})</span></td>"
            f"<td><code>{escape(str(record.get('address', '')))}</code></td>"
            f"<td>{escape(str(record.get('transport', '—')))}</td>"
            f"<td>{escape(str(record.get('rssi') if record.get('rssi') is not None else '—'))}</td>"
            f"<td>{escape(services)}</td>"
            f"<td>{escape(manufacturer)}</td>"
            f"<td>{escape(str(record.get('last_seen', '—')))}</td>"
            "</tr>"
        )
    adapter_rows = []
    for key, label in (("platform", "Sistema"), ("adapter", "Adaptador"), ("status", "Estado"),
                       ("powered", "Ligado"), ("discoverable", "Visível"), ("pairable", "Aceita pareamento")):
        if key in adapter:
            adapter_rows.append(f"<div class='metric'><span>{escape(label)}</span><strong>{escape(str(adapter[key]))}</strong></div>")
    if not adapter_rows:
        adapter_rows.append("<p class='muted'>Detalhes do adaptador indisponíveis neste sistema.</p>")

    generated = utc_now()
    html = f"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>BT SENTINEL — Relatório de Avaliação</title>
<style>
:root{{--bg:#080d16;--panel:#101a29;--line:#25354b;--text:#e7effa;--muted:#91a4bd;--accent:#51e0b3}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top right,#172a3a,var(--bg) 48%);color:var(--text);font:15px/1.6 system-ui,Segoe UI,sans-serif}}
main{{max-width:1200px;margin:0 auto;padding:42px 24px}}header{{border-bottom:1px solid var(--line);padding-bottom:28px;margin-bottom:24px}}
.eyebrow{{color:var(--accent);letter-spacing:.18em;font-size:12px;font-weight:700}}h1{{font-size:clamp(30px,5vw,48px);margin:8px 0}}h2{{font-size:18px;margin:0 0 16px}}.muted,header p{{color:var(--muted)}}
.panel{{background:rgba(16,26,41,.92);border:1px solid var(--line);border-radius:16px;padding:22px;margin:18px 0;overflow:hidden}}
.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}.metric{{padding:13px;border:1px solid var(--line);border-radius:12px;display:flex;flex-direction:column;gap:6px}}.metric span{{color:var(--muted);font-size:12px}}.metric strong{{overflow-wrap:anywhere}}
.table-wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;min-width:850px}}th,td{{text-align:left;padding:12px;border-bottom:1px solid var(--line);vertical-align:top}}th{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}}code{{color:var(--accent)}}
.notice{{border-left:3px solid var(--accent);padding:12px 16px;background:#112522;border-radius:5px;color:#ccece2}}footer{{color:var(--muted);font-size:12px;padding:24px 0}}
</style></head><body><main><header><div class="eyebrow">PAI JOÃO K DEV / BT SENTINEL</div>
<h1>Relatório de Inteligência Bluetooth</h1><p>Gerado em {escape(generated)} · Observações de descoberta e consulta local</p></header>
<div class="notice"><strong>Interpretação:</strong> metadados de descoberta não comprovam vulnerabilidade, possibilidade de exploração, propriedade do dispositivo ou identidade de usuário. Dispositivos podem usar endereços aleatorizados e anúncios incompletos.</div>
<section class="panel"><h2>Inventário · {len(devices)} dispositivo(s)</h2><div class="table-wrap"><table><thead><tr><th>Nome</th><th>Categoria estimada</th><th>Endereço / ID</th><th>Transporte</th><th>RSSI</th><th>Serviços anunciados</th><th>IDs de fabricante</th><th>Visto por último</th></tr></thead>
<tbody>{''.join(rows) if rows else '<tr><td colspan="8">Nenhum dispositivo registrado.</td></tr>'}</tbody></table></div></section>
<section class="panel"><h2>Retrato do adaptador local</h2><div class="metrics">{''.join(adapter_rows)}</div></section>
<section class="panel"><h2>Limites da avaliação</h2><p>A categoria é uma hipótese calculada a partir do nome e dos UUIDs anunciados; não confirma fabricante, modelo, dono, serviço acessível ou vulnerabilidade. Este relatório contém observações de rádio e uma fotografia local do adaptador. Não executa exploits, não se conecta aos dispositivos encontrados, não enumera serviços remotos, não escreve características GATT, não faz pareamento forçado, não injeta áudio, não falsifica endereços, não faz flooding e não executa negação de serviço.</p><p>Valide a postura de segurança com inventários de ativos fornecidos pelos responsáveis, avisos dos fabricantes e procedimentos controlados de avaliação.</p></section>
<footer>BT SENTINEL {escape(__version__)} · Projeto educacional · Somente ambientes autorizados</footer>
</main></body></html>"""
    output.write_text(html, encoding="utf-8")
    return output
