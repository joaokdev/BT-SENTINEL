from __future__ import annotations

import asyncio
import json
import platform
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
from .core import (
    append_audit_event,
    load_inventory,
    merge_inventory,
    merge_record,
    render_html_report,
    save_json_atomic,
    signal_label,
)
from .device_intel import classify_device
from .scanner import run_discovery
from .system_control import (
    control_media,
    open_bluetooth_settings,
    open_media_source,
    open_sound_settings,
)


class SentinelApp:
    """Portuguese-first terminal console for authorized Bluetooth observation."""

    def __init__(self, root: Path):
        self.root = root
        self.data_dir = root / "data"
        self.logs_dir = root / "logs"
        self.audit_log_path = self.logs_dir / "audit.jsonl"
        self.reports_dir = root / "reports"
        self.inventory_path = self.data_dir / "inventory.json"
        self.console = Console()
        self.session_devices: dict[str, dict[str, Any]] = {}
        self.scan_status = "Pronto"
        for directory in (self.data_dir, self.logs_dir, self.reports_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def banner(self) -> None:
        title = Text("PAI JOÃO K DEV", style="bold white")
        title.stylize("bold bright_cyan")
        brand = Text("B T   S E N T I N E L   /   4.0", style="bold bright_cyan")
        subtitle = Text("CENTRAL DE INTELIGÊNCIA BLUETOOTH", style="bold white")
        footer = Text("DESCOBERTA  •  INVENTÁRIO  •  CHECK-UP  •  ÁUDIO AUTORIZADO", style="dim")
        self.console.print(
            Panel(
                Align.center(Group(title, brand, subtitle, footer)),
                border_style="bright_cyan",
                box=box.DOUBLE,
                padding=(1, 2),
            )
        )

    def _pause(self) -> None:
        Prompt.ask("Pressione Enter para voltar ao menu", default="", console=self.console)

    def authorize(self) -> bool:
        self.console.print(
            Panel(
                "Use somente equipamentos seus ou ambientes em que você tenha autorização.\n"
                "A descoberta observa anúncios BLE e, no Linux, usa a descoberta padrão do BlueZ.\n"
                "O pareamento é concluído pelo Windows/Linux, com confirmação no aparelho.\n"
                "Os controles de mídia atuam na sessão/saída padrão do seu computador, não em um ID Bluetooth remoto.",
                title="[bold yellow]ANTES DE COMEÇAR · USO AUTORIZADO[/bold yellow]",
                border_style="yellow",
            )
        )
        confirmed = Confirm.ask("Confirmo que vou usar o programa somente em dispositivos/ambientes autorizados", default=False, console=self.console)
        if confirmed:
            append_audit_event(self.audit_log_path, "SESSAO_AUTORIZADA", {"modo": "interativo"})
        return confirmed

    def menu(self) -> str:
        table = Table(box=box.SIMPLE_HEAVY, show_header=False, expand=True, padding=(0, 1))
        table.add_column("Opção", style="bold bright_cyan", width=9)
        table.add_column("Módulo", style="bold white", min_width=25)
        table.add_column("O que faz", style="dim")
        rows = [
            ("[1]", "Descobrir dispositivos", "Varredura ao vivo e seleção após a coleta"),
            ("[2]", "Inteligência / inventário", "Classificação provável, metadados e histórico"),
            ("[3]", "Check-up do adaptador", "Verifica o Bluetooth deste computador"),
            ("[4]", "Parear dispositivo", "Abre o pareamento oficial do Windows/Linux"),
            ("[5]", "Central de áudio", "Saída Bluetooth, arquivo local e controles de mídia"),
            ("[6]", "Gerar relatório", "Cria um relatório HTML local"),
            ("[7]", "Ajuda e compatibilidade", "Explica o que cada sistema realmente suporta"),
            ("[0]", "Sair", "Encerra o BT SENTINEL"),
        ]
        for row in rows:
            table.add_row(*row)
        self.console.print(Panel(table, title="[bold bright_cyan]CENTRAL DE OPERAÇÕES[/bold bright_cyan]", border_style="bright_cyan"))
        return Prompt.ask("Escolha um módulo", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="1", console=self.console)

    def run(self) -> None:
        self.banner()
        if not self.authorize():
            self.console.print("[yellow]Autorização não confirmada. Sessão encerrada.[/yellow]")
            return
        actions = {
            "1": self.live_discovery,
            "2": self.inventory_view,
            "3": self.adapter_audit,
            "4": self.pair_device,
            "5": self.audio_center,
            "6": self.generate_report,
            "7": self.show_help,
        }
        while True:
            self.console.clear()
            self.banner()
            choice = self.menu()
            if choice == "0":
                self.console.print("[bright_cyan]Sessão encerrada. Obrigado por usar o BT SENTINEL.[/bright_cyan]")
                return
            try:
                actions[choice]()
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Operação interrompida pelo operador.[/yellow]")
            self._pause()

    def _translate_status(self, message: str) -> str:
        translations = {
            "Passive BLE advertisement listening": "Escuta passiva de anúncios BLE",
            "Passive BLE + standard Bluetooth Classic inquiry": "BLE passivo + descoberta padrão BlueZ",
            "Standard Bluetooth Classic inquiry": "Descoberta padrão BlueZ",
            "Pronto": "Pronto",
        }
        return translations.get(message, message)

    def live_discovery(self, duration: int | None = None, transports: str | None = None) -> list[dict[str, Any]]:
        self.console.print(Panel(
            "A varredura observa sinais e anúncios próximos. Ela não pareia, não se conecta e não controla os aparelhos encontrados.",
            title="[bold bright_cyan]DESCOBERTA AO VIVO[/bold bright_cyan]", border_style="bright_cyan"
        ))
        if duration is None:
            duration = IntPrompt.ask("Duração da busca em segundos", default=20, console=self.console)
        duration = max(5, min(duration, 120))
        if transports is None:
            if platform.system() == "Linux":
                transports = Prompt.ask(
                    "Modo de descoberta",
                    choices=["all", "ble", "bluez"],
                    default="all",
                    console=self.console,
                )
                self.console.print("[dim]BlueZ usa a descoberta do sistema; o resultado pode incluir LE e BR/EDR, conforme o adaptador e o BlueZ.[/dim]")
            else:
                transports = "ble"
                self.console.print("[dim]Neste Windows, a descoberta disponível pelo BT SENTINEL é BLE.[/dim]")

        self.session_devices = {}
        started = datetime.now(timezone.utc)
        errors: list[str] = []
        append_audit_event(self.audit_log_path, "DESCOBERTA_INICIADA", {"duracao_segundos": duration, "modo": transports})

        def update_record(record: dict[str, Any]) -> None:
            key = str(record.get("address", ""))
            if key:
                self.session_devices[key] = merge_record(self.session_devices.get(key), record)

        def status_update(message: str) -> None:
            self.scan_status = self._translate_status(message)

        def render_live() -> Group:
            devices = list(self.session_devices.values())
            table = self._device_table(devices, show_index=False)
            elapsed = int((datetime.now(timezone.utc) - started).total_seconds())
            headline = Text(
                f"{self.scan_status}   |   {min(elapsed, duration):02d}/{duration:02d}s   |   {len(devices)} dispositivo(s)",
                style="bold bright_cyan",
            )
            note = Text("A lista atualiza durante a busca · Ctrl+C cancela", style="dim")
            return Group(Panel(Group(headline, note), border_style="bright_cyan"), table)

        async def perform(live: Live) -> list[str]:
            task = asyncio.create_task(run_discovery(duration, transports, update_record, status_update))
            while not task.done():
                live.update(render_live(), refresh=True)
                await asyncio.sleep(0.25)
            result = await task
            live.update(render_live(), refresh=True)
            return result

        try:
            with Live(render_live(), console=self.console, refresh_per_second=8, transient=False) as live:
                errors = asyncio.run(perform(live))
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Busca interrompida.[/yellow]")
        except RuntimeError as exc:
            errors.append(str(exc))

        observed = list(self.session_devices.values())
        try:
            saved = merge_inventory(load_inventory(self.inventory_path), observed)
            save_json_atomic(self.inventory_path, saved)
        except (OSError, ValueError) as exc:
            self.console.print(f"[red]Não foi possível salvar o inventário: {exc}[/red]")

        append_audit_event(self.audit_log_path, "DESCOBERTA_FINALIZADA", {"dispositivos_observados": len(observed), "erros": len(errors)})
        self.console.print(Panel(
            f"[bold]{len(observed)}[/bold] dispositivo(s) observado(s).\nInventário salvo em: {self.inventory_path}",
            title="[bold green]BUSCA CONCLUÍDA[/bold green]", border_style="green"
        ))
        for error in errors:
            self.console.print(f"[yellow]Aviso: {error}[/yellow]")
        if observed:
            self.select_and_inspect(observed)
        elif not errors:
            self.console.print("[yellow]Nenhum anúncio foi recebido nesta busca. Confira o Bluetooth, o adaptador e tente novamente.[/yellow]")
        return observed

    def _device_table(self, devices: list[dict[str, Any]], show_index: bool = True) -> Table:
        table = Table(box=box.ROUNDED, expand=True, border_style="bright_cyan")
        if show_index:
            table.add_column("#", style="bold bright_cyan", justify="right", width=3)
        table.add_column("Dispositivo", min_width=14, max_width=25)
        table.add_column("Categoria provável", min_width=18, max_width=27)
        table.add_column("ID / endereço", style="cyan", min_width=17, max_width=28)
        table.add_column("RSSI", justify="right", width=6)
        table.add_column("Vistos", justify="right", width=6)
        ordered = sorted(devices, key=lambda row: str(row.get("name", "")).casefold())
        for index, item in enumerate(ordered, start=1):
            profile = classify_device(item)
            cells = [
                str(item.get("name") or "Sem nome")[:25],
                f"{profile['category']} ({profile['confidence'].lower()})",
                str(item.get("address", "—"))[:28],
                str(item.get("rssi")) if item.get("rssi") is not None else "—",
                str(item.get("seen_count", 1)),
            ]
            if show_index:
                table.add_row(str(index), *cells)
            else:
                table.add_row(*cells)
        if not devices:
            row = ["Nenhum dispositivo", "—", "—", "—", "—"]
            table.add_row(*((["—"] if show_index else []) + row))
        return table

    def _select_device(self, devices: list[dict[str, Any]], prompt: str = "Número do dispositivo (Enter para voltar)") -> dict[str, Any] | None:
        ordered = sorted(devices, key=lambda row: str(row.get("name", "")).casefold())
        if not ordered:
            self.console.print("[yellow]Nenhum dispositivo disponível. Faça uma descoberta primeiro.[/yellow]")
            return None
        self.console.print(self._device_table(ordered))
        selection = Prompt.ask(prompt, default="", console=self.console)
        if not selection:
            return None
        if not selection.isdigit() or not 1 <= int(selection) <= len(ordered):
            self.console.print("[yellow]Número inválido.[/yellow]")
            return None
        return ordered[int(selection) - 1]

    def select_and_inspect(self, devices: list[dict[str, Any]]) -> None:
        item = self._select_device(devices, "Qual dispositivo deseja analisar? (Enter para pular)")
        if item:
            self.inspect_device(item)

    def inspect_device(self, item: dict[str, Any]) -> None:
        profile = classify_device(item)
        table = Table(box=box.SIMPLE, show_header=False, expand=True)
        table.add_column("Campo", style="dim", width=24)
        table.add_column("Valor observado", overflow="fold")
        values = [
            ("Nome anunciado", item.get("name", "Sem nome")),
            ("ID / endereço", item.get("address", "—")),
            ("Transporte reportado", item.get("transport", "—")),
            ("RSSI", item.get("rssi", "—")),
            ("Sinal estimado", signal_label(item.get("rssi"))),
            ("Categoria provável", profile["category"]),
            ("Confiança da estimativa", profile["confidence"]),
            ("Primeira observação", item.get("first_seen", "—")),
            ("Última observação", item.get("last_seen", "—")),
            ("Quantidade de observações", item.get("seen_count", 1)),
            ("UUIDs anunciados", ", ".join(item.get("service_uuids", []) or []) or "Nenhum observado"),
            ("IDs de fabricante", ", ".join(str(k) for k in (item.get("manufacturer_data", {}) or {}).keys()) or "Nenhum observado"),
            ("Potência TX anunciada", item.get("tx_power", "—")),
        ]
        for key, value in values:
            table.add_row(key, str(value))
        evidence = "\n".join(f"• {line}" for line in profile["evidence"])
        self.console.print(Panel(table, title="[bold bright_cyan]FICHA DO DISPOSITIVO[/bold bright_cyan]", border_style="bright_cyan"))
        self.console.print(Panel(f"{evidence}\n\n[dim]{profile['disclaimer']}[/dim]", title="Inteligência observacional", border_style="blue"))
        append_audit_event(self.audit_log_path, "DISPOSITIVO_INSPECIONADO", {"transporte": str(item.get("transport", "desconhecido")), "categoria": profile["category"]})
        self.console.print("[dim]A classificação é uma hipótese baseada em nome/UUID. Não identifica dono, modelo exato, vulnerabilidade nem comprova que o aparelho aceita conexão.[/dim]")

    def inventory_view(self) -> None:
        try:
            devices = load_inventory(self.inventory_path)
        except ValueError as exc:
            self.console.print(f"[red]Inventário inválido: {exc}[/red]")
            return
        if not devices:
            self.console.print("[yellow]Inventário vazio. Execute primeiro uma descoberta.[/yellow]")
            return
        item = self._select_device(devices, "Selecione um dispositivo para ver a ficha (Enter para voltar)")
        if item:
            self.inspect_device(item)

    def adapter_audit(self) -> dict[str, Any]:
        result = audit_local_adapter()
        labels = {
            "platform": "Sistema operacional", "adapter": "Adaptador", "status": "Disponibilidade",
            "powered": "Rádio ligado", "discoverable": "Visível para outros", "pairable": "Aceita pareamento",
        }
        table = Table(box=box.ROUNDED, show_header=False, expand=True)
        table.add_column("Item", style="dim", width=25)
        table.add_column("Resultado")
        for key, label in labels.items():
            table.add_row(label, str(result.get(key, "não informado")))
        self.console.print(Panel(table, title="[bold bright_cyan]CHECK-UP DO BLUETOOTH LOCAL[/bold bright_cyan]", border_style="bright_cyan"))
        for detail in result.get("details", []):
            if isinstance(detail, dict):
                self.console.print(f"[dim]• {detail.get('name', 'Dispositivo')} — {detail.get('status', 'estado desconhecido')}[/dim]")
            else:
                self.console.print(Panel(str(detail), title="Detalhes retornados pelo sistema", border_style="blue"))
        save_json_atomic(self.data_dir / "adapter_audit.json", result)
        append_audit_event(self.audit_log_path, "CHECKUP_ADAPTADOR", {"plataforma": result.get("platform"), "status": result.get("status")})
        self.console.print(f"[dim]Resultado salvo em {self.data_dir / 'adapter_audit.json'}[/dim]")
        return result

    def pair_device(self) -> None:
        try:
            devices = load_inventory(self.inventory_path)
        except ValueError as exc:
            self.console.print(f"[red]{exc}[/red]")
            return
        item = self._select_device(devices, "Qual dispositivo seu/autorizado deseja parear? (Enter para voltar)")
        if not item:
            return
        self.console.print(Panel(
            f"Dispositivo selecionado: [bold]{item.get('name', 'Sem nome')}[/bold]\nID observado: [cyan]{item.get('address', '—')}[/cyan]\n\nO ID serve para reconhecer a observação. O pareamento real será feito pelo sistema operacional, com confirmação física/PIN quando exigido.",
            title="[bold yellow]PAREAMENTO NORMAL E AUTORIZADO[/bold yellow]", border_style="yellow"
        ))
        if not Confirm.ask("Este dispositivo é seu ou você tem autorização explícita para pareá-lo?", default=False, console=self.console):
            self.console.print("[yellow]Pareamento cancelado.[/yellow]")
            return
        success, message = open_bluetooth_settings()
        style = "green" if success else "yellow"
        self.console.print(f"[{style}]{message}[/{style}]")
        if success:
            append_audit_event(self.audit_log_path, "CONFIGURACOES_PAREAMENTO_ABERTAS", {"categoria": classify_device(item)["category"]})
            self.console.print("[dim]Na tela do sistema, encontre o nome do dispositivo, selecione Parear/Conectar e confirme o mesmo código nos dois aparelhos, quando aparecer.[/dim]")

    def audio_center(self) -> None:
        self.console.print(Panel(
            "Esta central controla a sessão de mídia ativa e o volume da saída padrão do seu computador.\n"
            "Depois de parear seu fone/caixa, escolha-o como saída de áudio nas configurações.\n"
            "Play/Pause/Próxima/Anterior dependem do player e do suporte do sistema ao controle de mídia.",
            title="[bold bright_cyan]CENTRAL DE ÁUDIO · DISPOSITIVOS SEUS[/bold bright_cyan]", border_style="bright_cyan"
        ))
        table = Table(box=box.SIMPLE, show_header=False, expand=True)
        table.add_column("Opção", style="bold bright_cyan", width=8)
        table.add_column("Ação")
        table.add_row("[1]", "Abrir configurações de saída de áudio")
        table.add_row("[2]", "Reproduzir / pausar")
        table.add_row("[3]", "Próxima faixa")
        table.add_row("[4]", "Faixa anterior")
        table.add_row("[5]", "Aumentar volume")
        table.add_row("[6]", "Diminuir volume")
        table.add_row("[7]", "Silenciar / reativar")
        table.add_row("[8]", "Abrir arquivo de áudio ou página do YouTube")
        table.add_row("[0]", "Voltar")
        self.console.print(table)
        choice = Prompt.ask("Escolha", choices=[str(n) for n in range(9)], default="0", console=self.console)
        if choice == "0":
            return
        if choice == "1":
            success, message = open_sound_settings()
        elif choice in {"2", "3", "4", "5", "6", "7"}:
            action_map = {"2": "play_pause", "3": "next", "4": "previous", "5": "volume_up", "6": "volume_down", "7": "mute"}
            success, message = control_media(action_map[choice])
            append_audit_event(self.audit_log_path, "CONTROLE_MIDIA_LOCAL", {"acao": action_map[choice], "sucesso": success})
        else:
            source = Prompt.ask("Caminho completo do arquivo ou URL HTTPS do YouTube", console=self.console)
            success, message = open_media_source(source)
            append_audit_event(self.audit_log_path, "FONTE_MIDIA_ABERTA", {"tipo": "url" if source.startswith("https://") else "arquivo", "sucesso": success})
        style = "green" if success else "yellow"
        self.console.print(f"[{style}]{message}[/{style}]")

    def generate_report(self) -> Path | None:
        try:
            devices = load_inventory(self.inventory_path)
        except ValueError as exc:
            self.console.print(f"[red]Inventário inválido: {exc}[/red]")
            return None
        adapter_path = self.data_dir / "adapter_audit.json"
        try:
            adapter = json.loads(adapter_path.read_text(encoding="utf-8")) if adapter_path.exists() else {}
        except (OSError, ValueError):
            adapter = {}
        output = self.reports_dir / "relatorio_bt_sentinel.html"
        path = render_html_report(devices, adapter, output)
        append_audit_event(self.audit_log_path, "RELATORIO_GERADO", {"quantidade_dispositivos": len(devices)})
        self.console.print(Panel(f"[bold green]Relatório criado[/bold green]\n{path.resolve()}\n\nAbra o arquivo no navegador.", border_style="green"))
        return path

    def show_help(self) -> None:
        system = platform.system()
        if system == "Windows":
            discovery = "BLE passivo pelo adaptador/driver Windows. A descoberta Classic ainda não está implementada nesta versão."
        elif system == "Linux":
            discovery = "BLE passivo pelo Bleak e descoberta do BlueZ via bluetoothctl. O modo BlueZ pode apresentar dispositivos LE e BR/EDR; o parser não deve ser tratado como confirmação do perfil do dispositivo."
        else:
            discovery = "Descoberta BLE não habilitada nesta versão."
        self.console.print(Panel(
            f"[bold]Descoberta[/bold]\n{discovery}\n\n"
            "[bold]Classificação[/bold]\nÉ uma estimativa por nome e UUID anunciado. Pode errar; não é identificação forense nem consulta de CVE.\n\n"
            "[bold]Pareamento[/bold]\nO BT SENTINEL abre a tela oficial do sistema. O usuário precisa confirmar a conexão nos aparelhos. Não há bypass, pareamento forçado ou acesso por MAC/ID.\n\n"
            "[bold]Áudio[/bold]\nO aplicativo abre o seletor de saída e envia comandos à sessão de mídia/volume do computador. O áudio sai pela saída padrão selecionada no Windows/Linux. Não injeta áudio em aparelhos nem controla dispositivos não pareados.\n\n"
            "[bold]Dados locais[/bold]\nInventário: data/inventory.json · Check-up: data/adapter_audit.json · Auditoria: logs/audit.jsonl · Relatórios: reports/.\n\n"
            "[bold]Não incluído[/bold]\nExploração, invasão, bypass de pareamento, captura de credenciais, escrita GATT, spoofing, flooding, interferência ou negação de serviço.",
            title=f"[bold bright_cyan]AJUDA · {system}[/bold bright_cyan]", border_style="bright_cyan"
        ))
