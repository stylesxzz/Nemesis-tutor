#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if ! python -c "import flask" >/dev/null 2>&1; then
  echo "Dependências ausentes. Execute primeiro: bash install_android.sh"
  exit 1
fi
echo "NEMESIS Tutor: http://127.0.0.1:8765"
echo "Mantenha o Termux aberto. Pressione Ctrl+C para encerrar."
if command -v termux-open-url >/dev/null 2>&1; then
  (sleep 2; termux-open-url "http://127.0.0.1:8765") >/dev/null 2>&1 &
fi
exec python mobile_app.py
