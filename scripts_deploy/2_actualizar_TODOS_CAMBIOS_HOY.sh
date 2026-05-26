#!/bin/bash
# ======================================================
# Actualiza eGarage copiando la carpeta de despliegue completa.
# Uso recomendado tras subir egarage_update_atlantareciclajes.zip:
#   cd /home/atlantareciclajes/egarage_update
#   unzip -o egarage_update_atlantareciclajes.zip
#   bash deploy_atlantareciclajes/scripts_deploy/2_actualizar_TODOS_CAMBIOS_HOY.sh
# ======================================================

set -e

PROJECT_PATH="${PROJECT_PATH:-/home/atlantareciclajes/apps/egarage/current}"
UPDATE_PATH="${UPDATE_PATH:-/home/atlantareciclajes/egarage_update}"
ZIP_PATH="${UPDATE_PATH}/egarage_update_atlantareciclajes.zip"
DEPLOY_PATH="${UPDATE_PATH}/deploy_atlantareciclajes"

echo "======================================================"
echo "ACTUALIZACION COMPLETA DE CAMBIOS DEL DIA"
echo "======================================================"

if [ ! -d "${PROJECT_PATH}" ]; then
    echo "ERROR: No existe PROJECT_PATH=${PROJECT_PATH}"
    exit 1
fi

if [ ! -d "${DEPLOY_PATH}" ]; then
    if [ -f "${ZIP_PATH}" ]; then
        echo "Descomprimiendo ${ZIP_PATH}..."
        cd "${UPDATE_PATH}"
        unzip -o "${ZIP_PATH}"
    else
        echo "ERROR: No existe ${DEPLOY_PATH} ni ${ZIP_PATH}"
        exit 1
    fi
fi

if [ ! -d "${DEPLOY_PATH}" ]; then
    echo "ERROR: El ZIP no contiene deploy_atlantareciclajes/"
    exit 1
fi

copy_dir() {
    local name="$1"
    if [ -d "${DEPLOY_PATH}/${name}" ]; then
        mkdir -p "${PROJECT_PATH}/${name}"
        cp -a "${DEPLOY_PATH}/${name}/." "${PROJECT_PATH}/${name}/"
        echo "OK: ${name}/"
    fi
}

copy_file() {
    local name="$1"
    if [ -f "${DEPLOY_PATH}/${name}" ]; then
        cp -a "${DEPLOY_PATH}/${name}" "${PROJECT_PATH}/${name}"
        echo "OK: ${name}"
    fi
}

copy_dir "taller"
copy_dir "templates"
copy_dir "gestion_taller"
copy_dir "static"
copy_dir "core"
copy_dir "ubicacion"
copy_dir "docs"
copy_dir "scripts_deploy"
copy_file "manage.py"
copy_file "requirements.txt"

cd "${PROJECT_PATH}"

echo ""
echo "Ejecutando checks..."
python manage.py check

echo ""
echo "Aplicando migraciones..."
python manage.py migrate

echo ""
echo "Recolectando static..."
python manage.py collectstatic --noinput

echo ""
echo "======================================================"
echo "ACTUALIZACION COMPLETA LISTA"
echo "Recuerda hacer Reload en el panel Web de DigitalOcean."
echo "======================================================"
