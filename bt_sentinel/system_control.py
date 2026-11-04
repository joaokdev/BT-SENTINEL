from __future__ import annotations

import os
import platform
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Any


MEDIA_KEYS = {
    "play_pause": 0xB3,
    "next": 0xB0,
    "previous": 0xB1,
    "volume_up": 0xAF,
    "volume_down": 0xAE,
    "mute": 0xAD,
}


def open_bluetooth_settings() -> tuple[bool, str]:
    """Open the operating system's trusted Bluetooth pairing UI."""
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile("ms-settings:bluetooth")  # type: ignore[attr-defined]
            return True, "Configurações de Bluetooth abertas. Faça o pareamento pelo Windows e confirme o código no aparelho."
        if system == "Linux":
            candidates = [
                ["blueman-manager"],
                ["gnome-control-center", "bluetooth"],
                ["systemsettings", "kcm_bluetooth"],
            ]
            for command in candidates:
                if shutil.which(command[0]):
                    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True, f"Gerenciador Bluetooth aberto ({command[0]}). Conclua o pareamento na interface do sistema."
            return False, "Nenhum gerenciador gráfico encontrado. Abra as Configurações do sistema > Bluetooth."
        if system == "Darwin":
            subprocess.Popen(["open", "x-apple.systempreferences:com.apple.BluetoothSettings"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Ajustes Bluetooth abertos. Conclua o pareamento no macOS."
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"Não foi possível abrir as configurações: {exc}"
    return False, f"Sistema não suportado: {system}. Abra manualmente as configurações Bluetooth."


def open_sound_settings() -> tuple[bool, str]:
    """Open sound output settings so the operator can select their paired audio device."""
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile("ms-settings:sound")  # type: ignore[attr-defined]
            return True, "Configurações de Som abertas. Selecione seu fone/caixa Bluetooth como saída padrão."
        if system == "Linux":
            candidates = [
                ["pavucontrol"],
                ["gnome-control-center", "sound"],
                ["systemsettings", "kcm_pulseaudio"],
            ]
            for command in candidates:
                if shutil.which(command[0]):
                    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True, f"Configurações de áudio abertas ({command[0]}). Selecione a saída Bluetooth."
            return False, "Instale/abra pavucontrol ou as Configurações > Som do ambiente gráfico."
        if system == "Darwin":
            subprocess.Popen(["open", "x-apple.systempreferences:com.apple.Sound-Settings"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Ajustes de Som abertos. Selecione sua saída Bluetooth."
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"Não foi possível abrir as configurações de som: {exc}"
    return False, f"Sistema não suportado: {system}. Abra manualmente as configurações de som."


def control_media(action: str) -> tuple[bool, str]:
    """Control the active local media session; never addresses a remote device by radio ID."""
    if action not in {"play_pause", "next", "previous", "volume_up", "volume_down", "mute"}:
        return False, "Comando de mídia inválido."

    system = platform.system()
    if system == "Windows":
        try:
            import ctypes
            key = MEDIA_KEYS[action]
            user32 = ctypes.windll.user32
            user32.keybd_event(key, 0, 0, 0)
            user32.keybd_event(key, 0, 2, 0)
            labels = {"play_pause": "Reproduzir/pausar", "next": "Próxima faixa", "previous": "Faixa anterior",
                      "volume_up": "Aumentar volume do sistema", "volume_down": "Diminuir volume do sistema", "mute": "Silenciar/reativar o sistema"}
            return True, f"Comando enviado à sessão de mídia/volume do Windows: {labels[action]}."
        except Exception as exc:  # pragma: no cover - Windows-only API
            return False, f"Não foi possível enviar o comando de mídia do Windows: {exc}"

    if system == "Linux":
        if action in {"play_pause", "next", "previous"}:
            playerctl = shutil.which("playerctl")
            if not playerctl:
                return False, "playerctl não encontrado. Instale-o para controlar sessões de mídia Linux."
            command = {"play_pause": "play-pause", "next": "next", "previous": "previous"}[action]
            try:
                result = subprocess.run([playerctl, command], capture_output=True, text=True, timeout=5, check=False)
                if result.returncode == 0:
                    return True, f"Comando enviado à sessão ativa por playerctl: {command}."
                return False, result.stderr.strip() or "Nenhuma sessão de mídia compatível respondeu."
            except (OSError, subprocess.TimeoutExpired) as exc:
                return False, f"Falha no controle de mídia: {exc}"

        wpctl = shutil.which("wpctl")
        pactl = shutil.which("pactl")
        if wpctl:
            command = {"volume_up": "+3%", "volume_down": "3%-", "mute": "toggle"}[action]
            args = [wpctl, "set-mute", "@DEFAULT_AUDIO_SINK@", command] if action == "mute" else [wpctl, "set-volume", "@DEFAULT_AUDIO_SINK@", command]
        elif pactl:
            command = {"volume_up": "+3%", "volume_down": "-3%", "mute": "toggle"}[action]
            args = [pactl, "set-sink-mute", "@DEFAULT_SINK@", command] if action == "mute" else [pactl, "set-sink-volume", "@DEFAULT_SINK@", command]
        else:
            return False, "Nem wpctl nem pactl foram encontrados para controlar o volume."
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=5, check=False)
            return (result.returncode == 0, "Comando aplicado à saída padrão do Linux." if result.returncode == 0 else result.stderr.strip())
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"Falha ao controlar volume: {exc}"

    return False, f"Controles de mídia ainda não implementados para {system}."


def open_media_source(source: str) -> tuple[bool, str]:
    """Open a local audio file in its default player or open an ordinary YouTube page."""
    candidate = source.strip()
    if candidate.startswith(("https://", "http://")):
        from urllib.parse import urlparse
        parsed = urlparse(candidate)
        host = (parsed.hostname or "").lower()
        allowed = host in {"youtube.com", "www.youtube.com", "music.youtube.com", "youtu.be"}
        if parsed.scheme != "https" or not allowed:
            return False, "Use uma URL HTTPS do YouTube: youtube.com, music.youtube.com ou youtu.be."
        webbrowser.open(candidate)
        return True, "Página do YouTube aberta no navegador. O áudio será reproduzido pela saída padrão do sistema."

    path = Path(candidate).expanduser()
    if not path.is_file():
        return False, "Arquivo não encontrado. Informe o caminho completo de um arquivo de áudio."
    allowed_extensions = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".wma"}
    if path.suffix.lower() not in allowed_extensions:
        return False, "Formato não reconhecido. Use WAV, MP3, OGG, FLAC, M4A, AAC ou WMA."
    try:
        if platform.system() == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif platform.system() == "Linux":
            opener = shutil.which("xdg-open")
            if not opener:
                return False, "xdg-open não encontrado. Abra o arquivo pelo seu player de áudio."
            subprocess.Popen([opener, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            return False, "Sistema operacional não suportado para abrir áudio."
        return True, "Arquivo aberto no player padrão. A saída selecionada no sistema recebe o áudio."
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"Não foi possível abrir o arquivo: {exc}"
