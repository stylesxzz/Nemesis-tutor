#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cat <<'EOF'

Instalação concluída.
Execute: ./start_linux.sh
Se estiver em Linux/Wayland e a captura de tela falhar, confira as permissões de captura do compositor.
EOF
