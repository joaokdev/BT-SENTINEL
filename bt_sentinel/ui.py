from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from .audit import audit_local_adapter
from .core import append_audit_event, load_inventory, merge_inventory, merge_record, render_html_report, save_json_atomic, signal_label
from .scanner import run_discovery


class SentinelApp:
    def __init__(self, root: Path):
        self.root = root
        self.data_dir = root / "data"
        self.logs_dir = root / "logs"
        self.audit_log_path = self.logs_dir / "audit.jsonl"
        self.reports_dir = root / "reports"
        self.inventory_path = self.data_dir / "inventory.json"
        self.console = Console()
        self.session_devices: dict[str, dict[str, Any]] = {}
        self.scan_status = "Standby"

    def banner(self) -> None:
        logo = Text("B T   / /   S E N T I N E L", style="bold bright_cyan")
        subtitle = Text("BLUETOOTH SECURITY OBSERVABILITY  //  v3.0.0", style="bold white")
        boundary = Text("PASSIVE BLE  •  CLASSIC INQUIRY  •  READ-ONLY AUDIT", style="dim")
        self.console.print(Panel(Align.center(Group(logo, subtitle, boundary)), border_style="bright_cyan", box=box.DOUBLE))

    def authorize(self) -> bool:
        self.console.print(Panel(
            "Use only with devices and radio environments you own or are explicitly authorized to assess.\n"
            "BLE uses passive listening; Bluetooth Classic uses standard inquiry transmissions where enabled.\n"
            "The scanner does not connect, pair, write characteristics, exploit, flood, or disrupt devices.\n"
            "Device names and identifiers may be personal or sensitive data.",
            title="[bold yellow]Authorization & operating boundaries[/bold yellow]",
            border_style="yellow",
        ))
        confirmed = Confirm.ask("I confirm that I am authorized to perform this assessment", default=False, console=self.console)
        if confirmed:
            append_audit_event(self.audit_log_path, "SESSION_AUTHORIZED", {"mode": "interactive"})
        return confirmed

    def menu(self) -> str:
        table = Table(box=box.SIMPLE_HEAVY, show_header=False, expand=True, padding=(0, 1))
        table.add_column("Option", style="bold bright_cyan", width=8)
        table.add_column("Action", style="white")
        table.add_column("Description", style="dim")
        table.add_row("[1]", "Live discovery", "Observe nearby BLE devices; optional Classic inquiry where supported")
        table.add_row("[2]", "Device inventory", "Browse saved observations and inspect one device")
        table.add_row("[3]", "Local adapter audit", "Read-only snapshot of this computer's Bluetooth settings")
        table.add_row("[4]", "Generate report", "Create a self-contained HTML assessment report")
        table.add_row("[5]", "Capabilities & help", "Review platform support and operating boundaries")
        table.add_row("[0]", "Exit", "Close the application")
        self.console.print(Panel(table, title="[bold bright_cyan]CONTROL CENTER[/bold bright_cyan]", border_style="bright_cyan"))
        return Prompt.ask("Select module", choices=["0", "1", "2", "3", "4", "5"], default="1", console=self.console)

    def run(self) -> None:
        self.banner()
        if not self.authorize():
            self.console.print("[yellow]Authorization not confirmed. Session closed.[/yellow]")
            return
        while True:
            self.console.clear()
            self.banner()
            choice = self.menu()
            if choice == "0":
                self.console.print("[bright_cyan]BT SENTINEL session closed.[/bright_cyan]")
                return
            if choice == "1":
                self.live_discovery()
            elif choice == "2":
                self.inventory_view()
            elif choice == "3":
                self.adapter_audit()
            elif choice == "4":
                self.generate_report()
            elif choice == "5":
                self.show_help()
            Prompt.ask("Press Enter to return to the control center", default="", console=self.console)

    def live_discovery(self, duration: int | None = None, transports: str | None = None) -> list[dict[str, Any]]:
        if duration is None:
            duration = IntPrompt.ask("Discovery window in seconds", default=18, console=self.console)
        duration = max(5, min(duration, 120))
        if transports is None:
            transports = Prompt.ask("Transports", choices=["all", "ble", "classic"], default="all", console=self.console)
        self.session_devices = {}
        started = datetime.now(timezone.utc)
        errors: list[str] = []
        append_audit_event(self.audit_log_path, "DISCOVERY_STARTED", {"duration_seconds": duration, "transports": transports})

        def update_record(record: dict[str, Any]) -> None:
            address = record["address"]
            self.session_devices[address] = merge_record(self.session_devices.get(address), record)

        def status_update(message: str) -> None:
            self.scan_status = message

        def render_live() -> Group:
            table = self._device_table(list(self.session_devices.values()), show_index=False)
            elapsed = int((datetime.now(timezone.utc) - started).total_seconds())
            headline = Text(f"{self.scan_status}  |  {min(elapsed, duration)}/{duration}s  |  {len(self.session_devices)} seen", style="bold bright_cyan")
            note = Text("BLE passive · Classic inquiry sends standard inquiry frames · Ctrl+C cancels", style="dim")
            return Group(Panel(Group(headline, note), border_style="bright_cyan"), table)

        async def perform() -> list[str]:
            discovery_task = asyncio.create_task(run_discovery(duration, transports, update_record, status_update))
            while not discovery_task.done():
                live.update(render_live(), refresh=True)
                await asyncio.sleep(0.25)
            result = await discovery_task
            live.update(render_live(), refresh=True)
            return result

        self.console.print("[bold bright_cyan]Starting live discovery...[/bold bright_cyan]")
        try:
            with Live(render_live(), console=self.console, refresh_per_second=8, transient=True) as live:
                errors = asyncio.run(perform())
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Discovery interrupted by operator.[/yellow]")
        except RuntimeError as exc:
            errors.append(str(exc))

        observed = list(self.session_devices.values())
        try:
            existing = load_inventory(self.inventory_path)
            merged = merge_inventory(existing, observed)
            save_json_atomic(self.inventory_path, merged)
        except (OSError, ValueError) as exc:
            self.console.print(f"[red]Could not save inventory: {exc}[/red]")

        self.console.print(Panel(f"[bold]{len(observed)}[/bold] device(s) observed in this session\nInventory: {self.inventory_path}", title="Discovery complete", border_style="green"))
        append_audit_event(self.audit_log_path, "DISCOVERY_FINISHED", {"observed_count": len(observed), "error_count": len(errors)})
        for error in errors:
            self.console.print(f"[yellow]• {error}[/yellow]")
        if observed:
            self.select_and_inspect(observed)
        return observed

    def _device_table(self, devices: list[dict[str, Any]], show_index: bool = True) -> Table:
        table = Table(box=box.ROUNDED, expand=True, border_style="blue")
        if show_index:
            table.add_column("#", style="bold bright_cyan", justify="right", width=2)
        table.add_column("Device", min_width=14)
        table.add_column("Address / ID", style="cyan", min_width=18)
        table.add_column("Type", width=9)
        table.add_column("RSSI", justify="right", width=5)
        table.add_column("Signal", width=7)
        table.add_column("Svc", justify="right", width=4)
        for index, item in enumerate(sorted(devices, key=lambda row: str(row.get("name", "")).casefold()), start=1):
            cells = [
                Text(str(item.get("name") or "Unknown")[:28]),
                Text(str(item.get("address", "—"))[:30]),
                Text(str(item.get("transport", "—"))),
                Text(str(item.get("rssi")) if item.get("rssi") is not None else "—"),
                Text(signal_label(item.get("rssi"))),
                Text(str(len(item.get("service_uuids", []) or []))),
            ]
            if show_index:
                table.add_row(str(index), *cells)
            else:
                table.add_row(*cells)
        if not devices:
            table.add_row(*(["—"] if show_index else []) + ["No devices observed", "—", "—", "—", "—", "—"])
        return table

    def select_and_inspect(self, devices: list[dict[str, Any]]) -> None:
        ordered = sorted(devices, key=lambda row: str(row.get("name", "")).casefold())
        self.console.print(self._device_table(ordered))
        selection = Prompt.ask("Device number to inspect (Enter to skip)", default="", console=self.console)
        if not selection:
            return
        if not selection.isdigit() or not 1 <= int(selection) <= len(ordered):
            self.console.print("[yellow]Invalid selection.[/yellow]")
            return
        self.inspect_device(ordered[int(selection) - 1])

    def inspect_device(self, item: dict[str, Any]) -> None:
        table = Table(box=box.SIMPLE, show_header=False, expand=True)
        table.add_column("Field", style="dim", width=22)
        table.add_column("Observed value", overflow="fold")
        values = [
            ("Name", item.get("name", "Unknown")),
            ("Address / ID", item.get("address", "—")),
            ("Transport", item.get("transport", "—")),
            ("RSSI", item.get("rssi", "—")),
            ("Signal estimate", signal_label(item.get("rssi"))),
            ("First seen", item.get("first_seen", "—")),
            ("Last seen", item.get("last_seen", "—")),
            ("Observations", item.get("seen_count", 1)),
            ("Advertised services", ", ".join(item.get("service_uuids", []) or []) or "None observed"),
            ("Manufacturer data", str(item.get("manufacturer_data", {}) or "None observed")),
            ("TX power", item.get("tx_power", "—")),
        ]
        for key, value in values:
            table.add_row(key, str(value))
        self.console.print(Panel(table, title="[bold bright_cyan]DEVICE OBSERVATION[/bold bright_cyan]", border_style="bright_cyan"))
        append_audit_event(self.audit_log_path, "DEVICE_INSPECTED", {"transport": str(item.get("transport", "unknown"))})
        self.console.print("[dim]Observation data only. It does not identify an owner or establish a vulnerability.[/dim]")

    def inventory_view(self) -> None:
        try:
            devices = load_inventory(self.inventory_path)
        except ValueError as exc:
            self.console.print(f"[red]{exc}[/red]")
            return
        self.console.print(self._device_table(devices))
        if devices:
            self.select_and_inspect(devices)
        else:
            self.console.print("[yellow]No saved observations yet. Run Live discovery first.[/yellow]")

    def adapter_audit(self) -> dict[str, Any]:
        result = audit_local_adapter()
        table = Table(box=box.ROUNDED, show_header=False)
        table.add_column("Property", style="dim", width=20)
        table.add_column("Observed value")
        for key in ("platform", "adapter", "status", "powered", "discoverable", "pairable"):
            table.add_row(key.replace("_", " ").title(), str(result.get(key, "unknown")))
        self.console.print(Panel(table, title="[bold bright_cyan]LOCAL ADAPTER AUDIT[/bold bright_cyan]", border_style="bright_cyan"))
        for detail in result.get("details", []):
            self.console.print(Panel(str(detail), title="Read-only details", border_style="blue"))
        save_json_atomic(self.data_dir / "adapter_audit.json", result)
        append_audit_event(self.audit_log_path, "LOCAL_ADAPTER_AUDIT", {"platform": result.get("platform"), "status": result.get("status")})
        self.console.print(f"[dim]Saved: {self.data_dir / 'adapter_audit.json'}[/dim]")
        return result

    def generate_report(self) -> Path | None:
        try:
            devices = load_inventory(self.inventory_path)
        except ValueError as exc:
            self.console.print(f"[red]{exc}[/red]")
            return None
        adapter_path = self.data_dir / "adapter_audit.json"
        try:
            import json
            adapter = json.loads(adapter_path.read_text(encoding="utf-8")) if adapter_path.exists() else {}
        except (OSError, ValueError):
            adapter = {}
        output = self.reports_dir / "assessment.html"
        path = render_html_report(devices, adapter, output)
        append_audit_event(self.audit_log_path, "HTML_REPORT_GENERATED", {"device_count": len(devices)})
        self.console.print(Panel(f"[bold green]Report generated[/bold green]\n{path.resolve()}\n\nOpen the file in your browser to review the report.", border_style="green"))
        return path

    def show_help(self) -> None:
        self.console.print(Panel(
            "[bold]BLE[/bold] discovery uses passive advertisement listening on supported Windows and Linux systems with a compatible adapter. It is not enabled on macOS because the selected Bleak backend does not support passive mode there.\n\n"
            "[bold]Bluetooth Classic[/bold] nearby inquiry is implemented through BlueZ on Linux. It sends standard inquiry transmissions and does not connect or pair with discovered devices.\n\n"
            "[bold]Local audit[/bold] is read-only. Windows reports Bluetooth Plug-and-Play devices; Linux reads bluetoothctl adapter state.\n\n"
            "[bold]Data[/bold] is stored locally in data/inventory.json, data/adapter_audit.json, logs/audit.jsonl, and reports/. Treat identifiers and manufacturer data as potentially sensitive.\n\n"
            "[bold]Not included[/bold]: forced pairing, GATT writes, remote service enumeration, exploits, address spoofing, audio injection, jamming, flooding, or DoS.",
            title="Capabilities & help", border_style="bright_cyan"))
