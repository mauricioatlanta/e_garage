#!/bin/bash
# ========================================
# SCRIPT: Verificar estado de migraciones en servidor
# ========================================
# Ejecutar en el servidor como usuario egarage
# Uso: ./VERIFICAR_MIGRACIONES_SERVIDOR.sh

echo "========================================="
echo "🔍 VERIFICANDO ESTADO DE MIGRACIONES"
echo "========================================="
echo ""

cd /srv/egarage

echo "📋 1. Estado de migraciones de la app 'taller':"
echo "----------------------------------------"
sudo -u egarage -H /srv/egarage/venv/bin/python manage.py showmigrations taller | tail -n 120

echo ""
echo "========================================="
echo "📋 2. Plan de migraciones pendientes:"
echo "----------------------------------------"
sudo -u egarage -H /srv/egarage/venv/bin/python manage.py migrate --plan | tail -n 120

echo ""
echo "========================================="
echo "✅ Verificación completada"
echo "========================================="
