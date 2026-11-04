#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "[!] Ambiente virtual não encontrado. Execute: bash scripts/setup_linux.sh"
  exit 1
fi

exec .venv/bin/python -m bt_sentinel
