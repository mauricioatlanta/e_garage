#!/bin/bash
# Script para corregir el error de AccountMiddleware en el servidor

RELEASE_DIR="/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg"

cd "$RELEASE_DIR" || exit 1

echo "🔍 Buscando archivos con AccountMiddleware..."
grep -r "allauth.account.middleware.AccountMiddleware" gestion_taller/settings* 2>/dev/null

echo ""
echo "🔧 Corrigiendo archivos..."

# Corregir gestion_taller/settings/base.py
if [ -f "gestion_taller/settings/base.py" ]; then
    sed -i 's/"allauth.account.middleware.AccountMiddleware",/# "allauth.account.middleware.AccountMiddleware",  # No disponible en allauth 65.9.0/' gestion_taller/settings/base.py
    echo "✅ gestion_taller/settings/base.py corregido"
fi

# Corregir gestion_taller/settings.py
if [ -f "gestion_taller/settings.py" ]; then
    sed -i 's/"allauth.account.middleware.AccountMiddleware",/# "allauth.account.middleware.AccountMiddleware",  # No disponible en allauth 65.9.0/' gestion_taller/settings.py
    echo "✅ gestion_taller/settings.py corregido"
fi

# Corregir gestion_taller/compacto/settings.py
if [ -f "gestion_taller/compacto/settings.py" ]; then
    sed -i 's/"allauth.account.middleware.AccountMiddleware",/# "allauth.account.middleware.AccountMiddleware",  # No disponible en allauth 65.9.0/' gestion_taller/compacto/settings.py
    echo "✅ gestion_taller/compacto/settings.py corregido"
fi

echo ""
echo "🔍 Verificando cambios..."
grep -n "AccountMiddleware" gestion_taller/settings/base.py gestion_taller/settings.py gestion_taller/compacto/settings.py 2>/dev/null | head -5

echo ""
echo "✅ Corrección completada. Reiniciando servidor..."
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
echo "✅ Servidor reiniciado"



