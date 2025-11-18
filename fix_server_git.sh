#!/bin/bash
# Script para actualizar el servidor y resolver conflictos de Git

RELEASE_DIR="/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg"

cd "$RELEASE_DIR" || exit 1

echo "🔄 Actualizando servidor desde Git..."

# Guardar cambios locales si existen
echo "📦 Guardando cambios locales..."
git stash push -m "Cambios locales antes de actualizar $(date +%Y%m%d_%H%M%S)" 2>/dev/null

# Hacer pull con merge
echo "📥 Haciendo pull desde origin/main..."
git pull origin main --no-rebase 2>&1

# Si hay conflictos, resolverlos aceptando la versión remota
if [ $? -ne 0 ]; then
    echo "⚠️  Hay conflictos. Resolviendo..."
    git checkout --theirs . 2>/dev/null
    git add -A
    git commit -m "Merge: resolver conflictos aceptando versión remota" 2>/dev/null
fi

# Verificar que el middleware esté correcto
echo "🔍 Verificando configuración..."
if grep -q "allauth.account.middleware.AccountMiddleware" gestion_taller/settings.py; then
    echo "✅ AccountMiddleware encontrado en settings.py"
else
    echo "⚠️  AccountMiddleware no encontrado"
fi

# Verificar que el template existe
if [ -f "templates/taller/includes/lang_switcher_cinematic.html" ]; then
    echo "✅ lang_switcher_cinematic.html existe"
else
    echo "⚠️  lang_switcher_cinematic.html no existe"
fi

# Verificar que views.py esté correcto
if python3 -m py_compile taller/documentos/views.py 2>/dev/null; then
    echo "✅ taller/documentos/views.py sintaxis correcta"
else
    echo "❌ Error de sintaxis en taller/documentos/views.py"
fi

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
echo "✅ Servidor reiniciado"

