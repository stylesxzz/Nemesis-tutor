#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERRO: não encontrei $PYTHON_BIN. Instale Python 3 e python3-venv primeiro."
  exit 1
fi

PY_VERSION="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "Python detectado: $("$PYTHON_BIN" --version)"
case "$PY_VERSION" in
  3.9|3.10|3.11|3.12|3.13) ;;
  *)
    echo "ERRO: PySide6 6.9.3 requer Python 3.9 a 3.13. Encontrado: $PY_VERSION"
    echo "Instale Python 3.11 ou 3.12 e execute: PYTHON_BIN=python3.12 ./repair_linux.sh"
    exit 1
    ;;
esac

if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
  echo "ERRO: o módulo venv não está disponível. Em Debian/Kali, execute: sudo apt install python3-venv"
  exit 1
fi

echo "Removendo somente o ambiente virtual .venv antigo..."
rm -rf .venv
"$PYTHON_BIN" -m venv .venv

VENV_PY=".venv/bin/python"
echo "Atualizando pip..."
"$VENV_PY" -m pip install --upgrade pip

echo "Instalando dependências com PySide6 6.9.3 (compatibilidade com CPUs antigas)..."
"$VENV_PY" -m pip install --no-cache-dir --only-binary=:all: -r requirements.txt

echo "Testando os módulos Qt antes de iniciar..."
"$VENV_PY" - <<'PY'
import sys
import PySide6
from PySide6.QtCore import qVersion
from PySide6.QtWidgets import QApplication
print("Python:", sys.version.split()[0])
print("PySide6:", PySide6.__version__)
print("Qt:", qVersion())
print("QtCore e QtWidgets: OK")
PY

echo
echo "Reparo concluído. Inicie com: ./start_linux.sh"
