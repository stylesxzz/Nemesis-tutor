#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v pkg >/dev/null 2>&1; then
  echo "Este instalador é para o Termux oficial no Android."
  exit 1
fi
pkg update
pkg install -y python
python -m pip install -r requirements-android.txt
echo
echo "Instalação concluída. Inicie com: bash start_android.sh"
