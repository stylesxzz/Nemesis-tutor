#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo "Ambiente virtual não encontrado. Execute ./install_linux.sh primeiro."
  exit 1
fi
source .venv/bin/activate
python -m pip uninstall -y PySide6 PySide6_Addons PySide6_Essentials shiboken6 || true
python -m pip install --no-cache-dir "PySide6==6.9.3"
python - <<'PY'
from PySide6.QtCore import qVersion
print(f"Qt instalado com sucesso: {qVersion()}")
PY
echo "Agora execute: ./start_linux.sh"
