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
        description="BT SENTINEL — inteligência Bluetooth, inventário e controles locais autorizados",
    )
    subparsers = parser.add_subparsers(dest="command")
    scan = subparsers.add_parser("scan", help="Executa descoberta Bluetooth ao vivo")
    scan.add_argument("--duration", type=int, default=18, help="Duração da busca em segundos (5–120)")
    scan.add_argument("--transport", choices=("all", "ble", "bluez", "classic"), default="all", help="all: BLE + BlueZ no Linux; ble: somente BLE; bluez: descoberta BlueZ (classic é alias legado)")
    subparsers.add_parser("inventory", help="Mostra o inventário salvo")
    subparsers.add_parser("audit", help="Faz check-up do adaptador Bluetooth local")
    report = subparsers.add_parser("report", help="Gera um relatório HTML local")
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
    app.console.print("[yellow]Use somente em dispositivos e ambientes autorizados. Pareamento e mídia são tratados pelo sistema operacional.[/yellow]")
    if not Confirm.ask("Confirmo que tenho autorização para esta avaliação", default=False, console=console):
        console.print("[yellow]Authorization not confirmed. Exiting.[/yellow]")
        raise SystemExit(1)
    append_audit_event(app.audit_log_path, "SESSAO_AUTORIZADA", {"modo": "linha_de_comando", "comando": args.command})

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
        append_audit_event(app.audit_log_path, "RELATORIO_GERADO", {"device_count": len(devices)})
        console.print(f"[green]Relatório gerado: {path.resolve()}[/green]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSessão interrompida.", file=sys.stderr)
        raise SystemExit(130)
