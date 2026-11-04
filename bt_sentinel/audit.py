from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
from typing import Any


def _run_read_only(argv: list[str], timeout: int = 12) -> str:
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def audit_local_adapter() -> dict[str, Any]:
    """Collect a conservative, read-only snapshot of the local Bluetooth host."""
    system = platform.system()
    result: dict[str, Any] = {
        "platform": f"{system} {platform.release()}",
        "adapter": "system-default",
        "status": "unknown",
        "powered": "unknown",
        "discoverable": "unknown",
        "pairable": "unknown",
        "details": [],
    }

    if system == "Linux":
        binary = shutil.which("bluetoothctl")
        if not binary:
            result["details"].append("bluetoothctl is not installed; local adapter state unavailable.")
            return result
        output = _run_read_only([binary, "show"])
        if not output:
            result["details"].append("No adapter details returned. Check adapter availability and permissions.")
            return result
        for key, field in (("Powered", "powered"), ("Discoverable", "discoverable"), ("Pairable", "pairable")):
            match = re.search(rf"(?im)^\s*{key}:\s*(yes|no)\s*$", output)
            if match:
                result[field] = match.group(1).lower()
        result["status"] = "available"
        result["details"].append(output[:5000])
        return result

    if system == "Windows":
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        if not powershell:
            result["details"].append("PowerShell was not found; adapter inventory unavailable.")
            return result
        command = (
            "Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | "
            "Select-Object Status,FriendlyName,InstanceId | ConvertTo-Json -Compress"
        )
        output = _run_read_only([powershell, "-NoProfile", "-NonInteractive", "-Command", command])
        try:
            parsed = json.loads(output) if output else []
            devices = parsed if isinstance(parsed, list) else ([parsed] if parsed else [])
            result["details"] = [
                {"status": str(item.get("Status", "unknown")),
                 "name": str(item.get("FriendlyName", "Bluetooth device")),
                 "instance_id": str(item.get("InstanceId", ""))[:180]}
                for item in devices
            ]
            result["status"] = "available" if devices else "unknown"
            if devices:
                result["adapter"] = "; ".join(item["name"] for item in result["details"][:3])
                result["powered"] = "unknown (Windows PnP status is not a radio power-state check)"
        except (json.JSONDecodeError, AttributeError, TypeError):
            result["details"].append("Windows Bluetooth PnP inventory could not be parsed.")
        return result

    if system == "Darwin":
        binary = shutil.which("system_profiler")
        output = _run_read_only([binary, "SPBluetoothDataType", "-json"]) if binary else ""
        if output:
            result["status"] = "available"
            result["details"].append(output[:5000])
        else:
            result["details"].append("system_profiler returned no Bluetooth adapter data.")
        return result

    result["details"].append("This operating system is not currently supported for adapter auditing.")
    return result
