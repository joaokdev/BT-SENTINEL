#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] Python 3.10+ não encontrado. Instale Python e python3-venv primeiro."
  exit 1
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e .

echo
echo "BT SENTINEL instalado. Inicie com: bash scripts/start_linux.sh"
if ! command -v bluetoothctl >/dev/null 2>&1; then
  echo "[!] bluetoothctl não encontrado. Instale o pacote BlueZ para descoberta Classic."
fi
