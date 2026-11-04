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
        return 0, "O modo BLE passivo não está disponível no backend selecionado do macOS; a busca foi ignorada."
    if system not in ("Windows", "Linux"):
        return 0, f"A descoberta BLE passiva não está habilitada neste sistema operacional: {system}."

    try:
        from bleak import BleakScanner
    except ImportError:
        return 0, "Bleak não está instalado. Execute: python -m pip install -r requirements.txt"

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
        return len(seen), f"Erro na descoberta BLE: {exc}"
    finally:
        try:
            await scanner.stop()
        except Exception:
            pass
    return len(seen), None


async def scan_bluez_linux(duration: int, on_device: UpdateCallback) -> tuple[int, str | None]:
    """Launches standard BlueZ discovery via bluetoothctl; Linux only."""
    if platform.system() != "Linux":
        return 0, "A descoberta BlueZ está disponível somente no Linux."
    binary = shutil.which("bluetoothctl")
    if not binary:
        return 0, "bluetoothctl não encontrado. Instale BlueZ para habilitar a descoberta do sistema."

    try:
        process = await asyncio.create_subprocess_exec(
            binary, "--timeout", str(duration), "scan", "on",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except OSError as exc:
        return 0, f"Não foi possível iniciar bluetoothctl: {exc}"

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
        return len(seen), f"Erro na descoberta BlueZ: {exc}"
    return len(seen), None


async def run_discovery(duration: int, transports: str, on_device: UpdateCallback,
                        on_status: Callable[[str], None]) -> list[str]:
    errors: list[str] = []
    tasks: list[asyncio.Task[tuple[int, str | None]]] = []
    system = platform.system()

    if transports in ("ble", "all"):
        tasks.append(asyncio.create_task(scan_ble(duration, on_device)))
    if transports in ("bluez", "classic", "all"):
        if system == "Linux":
            tasks.append(asyncio.create_task(scan_bluez_linux(duration, on_device)))
        elif transports in ("bluez", "classic"):
            errors.append("A descoberta BlueZ está disponível somente no Linux.")

    if transports == "all" and system == "Linux":
        on_status("Descoberta BLE passiva + BlueZ")
    elif transports in ("bluez", "classic"):
        on_status("Descoberta padrão BlueZ")
    else:
        on_status("Escuta passiva de anúncios BLE")

    results = await asyncio.gather(*tasks)
    errors.extend(message for _, message in results if message)
    return errors


# Backward-compatible alias for callers that used the earlier internal name.
scan_classic_linux = scan_bluez_linux
