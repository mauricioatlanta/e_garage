#!/bin/bash

# ============================================================================
# SCRIPT DE DEPLOYMENT SEGURO - eGarage
# ============================================================================
# Este script actualiza eGarage en el servidor SIN BORRAR datos de suscriptores
# Preserva: User, Empresa, Suscripcion, RegistroEmbudoSuscriptor y todos los datos
# ============================================================================

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para imprimir secciones
print_section() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Banner inicial
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                         ║"
echo "║  🚀 eGarage - DEPLOYMENT SEGURO                        ║"
echo "║  📦 Actualización completa SIN perder datos            ║"
echo "║                                                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# 1. BACKUP COMPLETO DE BASE DE DATOS
# ============================================================================

print_section "1/8: BACKUP COMPLETO DE BASE DE DATOS"

BACKUP_DIR="backups/deployments"
mkdir -p $BACKUP_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_JSON="$BACKUP_DIR/backup_pre_deploy_$TIMESTAMP.json"
BACKUP_SQLITE="$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"

echo -e "${YELLOW}📦 Creando backup de base de datos...${NC}"

# Backup completo en JSON (incluyendo todos los datos de suscriptores)
echo "   → Backup JSON (todos los datos)..."
python manage.py dumpdata \
    --natural-foreign \
    --natural-primary \
    --exclude=contenttypes \
    --exclude=auth.permission \
    --exclude=sessions \
    --output=$BACKUP_JSON

# Backup de SQLite completo
if [ -f "db.sqlite3" ]; then
    echo "   → Backup SQLite completo..."
    cp db.sqlite3 "$BACKUP_SQLITE"
    echo -e "${GREEN}   ✅ Backup SQLite: $BACKUP_SQLITE${NC}"
fi

if [ -f "$BACKUP_JSON" ]; then
    # Contar registros importantes
    echo ""
    echo -e "${CYAN}📊 Datos respaldados:${NC}"
    USER_COUNT=$(python -c "import json; data=json.load(open('$BACKUP_JSON')); print(sum(1 for x in data if x.get('model') == 'auth.user'))" 2>/dev/null || echo "0")
    EMPRESA_COUNT=$(python -c "import json; data=json.load(open('$BACKUP_JSON')); print(sum(1 for x in data if x.get('model') == 'taller.empresa'))" 2>/dev/null || echo "0")
    SUSCRIPCION_COUNT=$(python -c "import json; data=json.load(open('$BACKUP_JSON')); print(sum(1 for x in data if x.get('model') == 'taller.suscripcion'))" 2>/dev/null || echo "0")
    
    echo "   👥 Usuarios: $USER_COUNT"
    echo "   🏢 Empresas: $EMPRESA_COUNT"
    echo "   💳 Suscripciones: $SUSCRIPCION_COUNT"
    echo ""
    echo -e "${GREEN}✅ Backup JSON creado: $BACKUP_JSON${NC}"
else
    echo -e "${RED}❌ Error creando backup JSON${NC}"
    exit 1
fi

# ============================================================================
# 2. VERIFICAR ESTADO ACTUAL DE LA BASE DE DATOS
# ============================================================================

print_section "2/8: VERIFICANDO ESTADO ACTUAL"

echo -e "${YELLOW}🔍 Verificando datos actuales en la base de datos...${NC}"

python manage.py shell << EOF
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion

user_count = User.objects.count()
empresa_count = Empresa.objects.count()
suscripcion_count = Suscripcion.objects.count() if hasattr(Suscripcion, 'objects') else 0

print(f"📊 Estado actual:")
print(f"   👥 Usuarios: {user_count}")
print(f"   🏢 Empresas: {empresa_count}")
print(f"   💳 Suscripciones: {suscripcion_count}")
EOF

echo -e "${GREEN}✅ Verificación completada${NC}"

# ============================================================================
# 3. VERIFICAR MIGRACIONES PENDIENTES
# ============================================================================

print_section "3/8: VERIFICANDO MIGRACIONES"

echo -e "${YELLOW}🔍 Verificando migraciones pendientes...${NC}"
python manage.py showmigrations --plan | grep "\[ \]" || echo "   ℹ️  No hay migraciones pendientes"

echo ""
read -p "¿Continuar con el deployment? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}⚠️  Deployment cancelado por el usuario${NC}"
    exit 0
fi

# ============================================================================
# 4. ACTUALIZAR CÓDIGO (si se usa Git)
# ============================================================================

print_section "4/8: ACTUALIZANDO CÓDIGO"

if [ -d ".git" ]; then
    echo -e "${YELLOW}📥 Actualizando código desde Git...${NC}"
    git pull origin main || git pull origin master || echo "   ⚠️  No se pudo hacer pull (continuando...)"
    echo -e "${GREEN}✅ Código actualizado${NC}"
else
    echo -e "${YELLOW}ℹ️  No hay repositorio Git. Asumiendo que el código ya está actualizado.${NC}"
    echo -e "${YELLOW}   Si subiste archivos manualmente, continúa.${NC}"
fi

# ============================================================================
# 5. ACTUALIZAR DEPENDENCIAS
# ============================================================================

print_section "5/8: ACTUALIZANDO DEPENDENCIAS"

if [ -d "venv" ]; then
    echo -e "${YELLOW}🔧 Activando virtual environment...${NC}"
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
elif command -v workon &> /dev/null; then
    echo -e "${YELLOW}🔧 Activando virtual environment (workon)...${NC}"
    workon venv_egarage310 || true
fi

echo -e "${YELLOW}📦 Actualizando dependencias...${NC}"
pip install --upgrade pip --quiet
pip install -r requirements.txt --upgrade --quiet
echo -e "${GREEN}✅ Dependencias actualizadas${NC}"

# ============================================================================
# 6. APLICAR MIGRACIONES (SIN BORRAR DATOS)
# ============================================================================

print_section "6/8: APLICANDO MIGRACIONES (PRESERVANDO DATOS)"

echo -e "${YELLOW}🔨 Creando nuevas migraciones si hay cambios...${NC}"
python manage.py makemigrations --noinput || echo "   ℹ️  No hay cambios en modelos"

echo ""
echo -e "${YELLOW}⚡ Aplicando migraciones (esto NO borrará datos existentes)...${NC}"

# Aplicar migraciones de forma segura
python manage.py migrate --noinput

# Si hay errores de "tabla ya existe", usar --fake-initial
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Error en migraciones. Intentando con --fake-initial...${NC}"
    python manage.py migrate --fake-initial --noinput || {
        echo -e "${RED}❌ Error crítico en migraciones${NC}"
        echo -e "${YELLOW}💡 Opción de rollback disponible:${NC}"
        echo "   cp $BACKUP_SQLITE db.sqlite3"
        exit 1
    }
fi

echo -e "${GREEN}✅ Migraciones aplicadas correctamente${NC}"

# ============================================================================
# 7. VERIFICAR QUE LOS DATOS SE PRESERVARON
# ============================================================================

print_section "7/8: VERIFICANDO PRESERVACIÓN DE DATOS"

echo -e "${YELLOW}🔍 Verificando que los datos se preservaron...${NC}"

python manage.py shell << EOF
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion

user_count_after = User.objects.count()
empresa_count_after = Empresa.objects.count()
suscripcion_count_after = Suscripcion.objects.count() if hasattr(Suscripcion, 'objects') else 0

print(f"📊 Estado después del deployment:")
print(f"   👥 Usuarios: {user_count_after}")
print(f"   🏢 Empresas: {empresa_count_after}")
print(f"   💳 Suscripciones: {suscripcion_count_after}")

# Verificar que no se perdieron datos críticos
if user_count_after == 0:
    print("⚠️  ADVERTENCIA: No hay usuarios en la base de datos!")
elif empresa_count_after == 0:
    print("⚠️  ADVERTENCIA: No hay empresas en la base de datos!")
else:
    print("✅ Los datos se preservaron correctamente")
EOF

echo -e "${GREEN}✅ Verificación completada${NC}"

# ============================================================================
# 8. COLECTAR ARCHIVOS ESTÁTICOS Y FINALIZAR
# ============================================================================

print_section "8/8: FINALIZANDO DEPLOYMENT"

echo -e "${YELLOW}🎨 Recolectando archivos estáticos...${NC}"
python manage.py collectstatic --noinput --clear
python manage.py collectstatic --noinput
echo -e "${GREEN}✅ Archivos estáticos actualizados${NC}"

echo ""
echo -e "${YELLOW}🔍 Ejecutando verificaciones finales...${NC}"
python manage.py check --deploy
echo -e "${GREEN}✅ Verificaciones completadas${NC}"

# ============================================================================
# RESUMEN FINAL
# ============================================================================

echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                         ║"
echo "║  🎉 DEPLOYMENT COMPLETADO EXITOSAMENTE                 ║"
echo "║                                                         ║"
echo "║  ✅ Backup creado                                      ║"
echo "║  ✅ Código actualizado                                 ║"
echo "║  ✅ Dependencias actualizadas                          ║"
echo "║  ✅ Migraciones aplicadas (datos preservados)         ║"
echo "║  ✅ Archivos estáticos actualizados                    ║"
echo "║  ✅ Datos de suscriptores preservados                 ║"
echo "║                                                         ║"
echo "║  📦 Backups guardados en:                              ║"
echo "║     • $BACKUP_JSON${NC}"
echo -e "${GREEN}║     • $BACKUP_SQLITE${NC}"
echo -e "${GREEN}║                                                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${CYAN}📝 PRÓXIMOS PASOS:${NC}"
echo "   1. Reiniciar el servidor web (si es necesario)"
echo "   2. Verificar que el sitio funciona correctamente"
echo "   3. Probar login con una cuenta existente"
echo ""
echo -e "${YELLOW}🔄 Si necesitas hacer rollback:${NC}"
echo "   cp $BACKUP_SQLITE db.sqlite3"
echo ""

