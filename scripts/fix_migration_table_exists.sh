#!/bin/bash
# Script para resolver error "table already exists" en migraciones
# Uso: ./scripts/fix_migration_table_exists.sh

echo "🔧 Solucionando error de migración: tabla ya existe"
echo "=================================================="

# 1. Verificar estado actual de migraciones
echo ""
echo "📋 Paso 1: Verificando estado de migraciones..."
python manage.py showmigrations taller | head -20

# 2. Aplicar migraciones con --fake-initial
echo ""
echo "🔄 Paso 2: Aplicando migraciones con --fake-initial..."
python manage.py migrate --fake-initial

if [ $? -eq 0 ]; then
    echo "✅ Migraciones iniciales marcadas como aplicadas"
else
    echo "⚠️  Hubo un problema. Continuando con migraciones normales..."
fi

# 3. Aplicar migraciones pendientes
echo ""
echo "🔄 Paso 3: Aplicando migraciones pendientes..."
python manage.py migrate

if [ $? -eq 0 ]; then
    echo "✅ Todas las migraciones aplicadas correctamente"
else
    echo "❌ Error al aplicar migraciones. Revisa el output anterior."
    exit 1
fi

# 4. Verificar estado final
echo ""
echo "📋 Paso 4: Estado final de migraciones..."
python manage.py showmigrations taller | grep -E "\[X\]|\[ \]"

echo ""
echo "✅ Proceso completado"









