from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

from .core import append_audit_event, load_inventory, render_html_report
from .ui import SentinelApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bt-sentinel",
        description="BT SENTINEL — interactive Bluetooth inventory with passive BLE and local assessment",
    )
    subparsers = parser.add_subparsers(dest="command")
    scan = subparsers.add_parser("scan", help="Run live Bluetooth discovery")
    scan.add_argument("--duration", type=int, default=18, help="Discovery window in seconds (5–120)")
    scan.add_argument("--transport", choices=("all", "ble", "classic"), default="all")
    subparsers.add_parser("inventory", help="Show the saved inventory")
    subparsers.add_parser("audit", help="Audit the local Bluetooth adapter")
    report = subparsers.add_parser("report", help="Generate a self-contained HTML report")
    report.add_argument("--output", type=Path, default=None)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    current = Path.cwd()
    root = current if (current / "pyproject.toml").exists() and (current / "bt_sentinel").is_dir() else (Path.home() / ".bt-sentinel")
    root.mkdir(parents=True, exist_ok=True)
    app = SentinelApp(root)
    console = Console()

    if args.command is None:
        app.run()
        return

    app.banner()
    app.console.print("[yellow]Authorized environments only. Passive BLE, standard Classic inquiry on Linux, and read-only local checks.[/yellow]")
    if not Confirm.ask("Confirm authorization for this assessment", default=False, console=console):
        console.print("[yellow]Authorization not confirmed. Exiting.[/yellow]")
        raise SystemExit(1)
    append_audit_event(app.audit_log_path, "SESSION_AUTHORIZED", {"mode": "command_line", "command": args.command})

    if args.command == "scan":
        app.live_discovery(duration=max(5, min(args.duration, 120)), transports=args.transport)
    elif args.command == "inventory":
        app.inventory_view()
    elif args.command == "audit":
        app.adapter_audit()
    elif args.command == "report":
        try:
            devices = load_inventory(app.inventory_path)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise SystemExit(2) from exc
        adapter_path = app.data_dir / "adapter_audit.json"
        adapter = {}
        if adapter_path.exists():
            import json
            try:
                adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                adapter = {}
        output = args.output or (app.reports_dir / "assessment.html")
        path = render_html_report(devices, adapter, output)
        append_audit_event(app.audit_log_path, "HTML_REPORT_GENERATED", {"device_count": len(devices)})
        console.print(f"[green]Report generated: {path.resolve()}[/green]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSession interrupted.", file=sys.stderr)
        raise SystemExit(130)
