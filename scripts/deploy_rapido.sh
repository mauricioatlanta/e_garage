#!/bin/bash
# Versión simplificada del deployment - ejecutar directamente en el servidor

set -e

echo "🚀 DEPLOYMENT RÁPIDO - eGarage"
echo "================================"
echo ""

# 1. Backup
echo "1️⃣  Creando backup..."
mkdir -p backups/deployments
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_SQLITE="backups/deployments/db_backup_$TIMESTAMP.sqlite3"
cp db.sqlite3 "$BACKUP_SQLITE"
echo "✅ Backup: $BACKUP_SQLITE"
echo ""

# 2. Actualizar código
echo "2️⃣  Actualizando código..."
if [ -d ".git" ]; then
    git pull origin main || git pull origin master || echo "⚠️  No se pudo hacer pull"
else
    echo "ℹ️  No hay Git, asumiendo código actualizado"
fi
echo ""

# 3. Dependencias
echo "3️⃣  Actualizando dependencias..."
pip install -r requirements.txt --upgrade --quiet
echo "✅ Dependencias actualizadas"
echo ""

# 4. Migraciones
echo "4️⃣  Aplicando migraciones..."
python manage.py makemigrations --noinput || echo "ℹ️  No hay cambios"
python manage.py migrate --noinput
echo "✅ Migraciones aplicadas"
echo ""

# 5. Estáticos
echo "5️⃣  Recolectando estáticos..."
python manage.py collectstatic --noinput
echo "✅ Estáticos actualizados"
echo ""

# 6. Verificar datos
echo "6️⃣  Verificando datos..."
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
print(f"✅ Usuarios: {User.objects.count()}")
print(f"✅ Empresas: {Empresa.objects.count()}")
EOF

echo ""
echo "🎉 DEPLOYMENT COMPLETADO"
echo ""
echo "⚠️  IMPORTANTE:"
echo "1. Verifica WSGI en PythonAnywhere → Web → WSGI configuration file"
echo "2. Recarga la aplicación web (botón verde 'Reload')"
echo "3. Prueba /ar/ y /uy/ en el navegador"
echo ""
