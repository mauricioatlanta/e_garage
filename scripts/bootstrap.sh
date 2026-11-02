#!/usr/bin/env bash
# Recrea el entorno virtual de desarrollo para eGarage.
# Requiere Python 3.11 o 3.12 — Django 4.2 no soporta Python 3.13+.
set -euo pipefail

# ── Validar versión de Python ─────────────────────────────────────────────────
PYTHON_BIN="${PYTHON:-python3}"

_ver=$("$PYTHON_BIN" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
_major=$(echo "$_ver" | cut -d. -f1)
_minor=$(echo "$_ver" | cut -d. -f2)

if [[ "$_major" -ne 3 ]] || [[ "$_minor" -lt 11 ]] || [[ "$_minor" -gt 12 ]]; then
    echo ""
    echo "[eGarage] Error: Python $_ver no está soportado."
    echo "          Versiones requeridas: 3.11 o 3.12."
    echo ""
    echo "  Opciones:"
    echo "    pyenv:    pyenv install 3.12 && pyenv local 3.12"
    echo "    apt:      sudo apt install python3.12 python3.12-venv"
    echo "    deadsnakes: sudo add-apt-repository ppa:deadsnakes/ppa"
    echo "                sudo apt install python3.12 python3.12-venv"
    echo ""
    echo "  Luego vuelve a ejecutar:"
    echo "    PYTHON=python3.12 bash scripts/bootstrap.sh"
    echo ""
    exit 1
fi

echo "[eGarage] Usando Python $_ver ($PYTHON_BIN)"

# ── Recrear venv ──────────────────────────────────────────────────────────────
VENV_DIR=".venv"

if [[ -d "$VENV_DIR" ]]; then
    echo "[eGarage] Eliminando venv existente en $VENV_DIR ..."
    rm -rf "$VENV_DIR"
fi

echo "[eGarage] Creando venv ..."
"$PYTHON_BIN" -m venv "$VENV_DIR"

# Activar para este script
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "[eGarage] Instalando dependencias ..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if [[ -f requirements-dev.txt ]]; then
    pip install -r requirements-dev.txt --quiet
fi

echo ""
echo "[eGarage] Entorno listo."
echo ""
echo "  Activa el entorno con:"
echo "    source .venv/bin/activate"
echo ""
echo "  Verifica la versión:"
echo "    python --version"
echo ""
