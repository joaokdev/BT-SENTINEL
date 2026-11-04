from __future__ import annotations

import asyncio
import platform
import shutil
from typing import Any, Callable

from .core import advertisement_to_record, merge_record, parse_classic_device_line

UpdateCallback = Callable[[dict[str, Any]], None]


async def scan_ble(duration: int, on_device: UpdateCallback) -> tuple[int, str | None]:
    """Listen for BLE advertisements only. Does not connect or issue GATT requests."""
    system = platform.system()
    if system == "Darwin":
        return 0, "Passive BLE mode is not supported on macOS by the selected Bleak backend; scanning was skipped."
    if system not in ("Windows", "Linux"):
        return 0, f"Passive BLE discovery is not enabled for this operating system: {system}."

    try:
        from bleak import BleakScanner
    except ImportError:
        return 0, "Bleak is not installed. Run: python -m pip install -r requirements.txt"

    seen: dict[str, dict[str, Any]] = {}

    def detection_callback(device: Any, advertisement: Any) -> None:
        try:
            record = advertisement_to_record(device, advertisement)
            address = record["address"]
            seen[address] = merge_record(seen.get(address), record)
            on_device(record)
        except (TypeError, ValueError, AttributeError):
            return

    scanner = BleakScanner(detection_callback=detection_callback, scanning_mode="passive")
    try:
        await scanner.start()
        await asyncio.sleep(duration)
    except Exception as exc:
        return len(seen), f"BLE scan error: {exc}"
    finally:
        try:
            await scanner.stop()
        except Exception:
            pass
    return len(seen), None


async def scan_classic_linux(duration: int, on_device: UpdateCallback) -> tuple[int, str | None]:
    """Passive inquiry through BlueZ bluetoothctl; Linux only."""
    if platform.system() != "Linux":
        return 0, "Classic nearby discovery is currently supported only on Linux/BlueZ."
    binary = shutil.which("bluetoothctl")
    if not binary:
        return 0, "bluetoothctl not found. Install BlueZ to enable Classic discovery."

    try:
        process = await asyncio.create_subprocess_exec(
            binary, "--timeout", str(duration), "scan", "on",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except OSError as exc:
        return 0, f"Could not start bluetoothctl: {exc}"

    seen: dict[str, dict[str, Any]] = {}
    try:
        assert process.stdout is not None
        while True:
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=duration + 5)
            except asyncio.TimeoutError:
                process.terminate()
                break
            if not line:
                break
            record = parse_classic_device_line(line.decode("utf-8", errors="replace").strip())
            if record:
                address = record["address"]
                seen[address] = merge_record(seen.get(address), record)
                on_device(record)
        try:
            await asyncio.wait_for(process.wait(), timeout=3)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
    except asyncio.CancelledError:
        process.terminate()
        await process.wait()
        raise
    except Exception as exc:
        if process.returncode is None:
            process.terminate()
            await process.wait()
        return len(seen), f"Classic scan error: {exc}"
    return len(seen), None


async def run_discovery(duration: int, transports: str, on_device: UpdateCallback,
                        on_status: Callable[[str], None]) -> list[str]:
    errors: list[str] = []
    tasks: list[asyncio.Task[tuple[int, str | None]]] = []
    system = platform.system()

    if transports in ("ble", "all"):
        tasks.append(asyncio.create_task(scan_ble(duration, on_device)))
    if transports in ("classic", "all"):
        if system == "Linux":
            tasks.append(asyncio.create_task(scan_classic_linux(duration, on_device)))
        elif transports == "classic":
            errors.append("Bluetooth Classic inquiry is available only on Linux with BlueZ.")

    if transports == "all" and system == "Linux":
        on_status("Passive BLE + standard Bluetooth Classic inquiry")
    elif transports == "classic":
        on_status("Standard Bluetooth Classic inquiry")
    else:
        on_status("Passive BLE advertisement listening")

    results = await asyncio.gather(*tasks)
    errors.extend(message for _, message in results if message)
    return errors
