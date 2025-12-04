#!/bin/bash
# Script para solucionar error de migración "table taller_categoriaservicio already exists"
# Uso: ./fix_migration_categoria.sh

set -e

echo "🔧 Solucionando error de migración categoriaservicio..."
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: No estás en el directorio del proyecto Django${NC}"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d "../venv" ] || [ -d "venv" ]; then
    echo -e "${YELLOW}Activando entorno virtual...${NC}"
    source venv/bin/activate 2>/dev/null || source ../venv/bin/activate 2>/dev/null || true
fi

# Hacer backup de la base de datos
if [ -f "db.sqlite3" ]; then
    BACKUP_NAME="db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}Haciendo backup de la base de datos...${NC}"
    cp db.sqlite3 "$BACKUP_NAME"
    echo -e "${GREEN}✓ Backup creado: $BACKUP_NAME${NC}"
fi

echo ""
echo -e "${YELLOW}Verificando estado de migraciones...${NC}"
python manage.py showmigrations taller | head -20

echo ""
echo -e "${YELLOW}Verificando si la tabla existe en la base de datos...${NC}"
python manage.py dbshell << EOF
.tables | grep categoriaservicio
.quit
EOF

echo ""
read -p "¿La tabla 'taller_categoriaservicio' existe? (s/n): " tabla_existe

if [ "$tabla_existe" = "s" ] || [ "$tabla_existe" = "S" ]; then
    echo ""
    echo -e "${YELLOW}La tabla existe. Verificando qué migración la crea...${NC}"
    
    # Buscar migración inicial
    if [ -f "taller/migrations/0001_initial_migration.py" ]; then
        echo -e "${YELLOW}Marcando migración inicial como aplicada (fake)...${NC}"
        python manage.py migrate taller 0001 --fake || true
    fi
    
    echo ""
    echo -e "${YELLOW}Aplicando migraciones pendientes...${NC}"
    python manage.py migrate || {
        echo -e "${RED}Error al aplicar migraciones. Revisa el error arriba.${NC}"
        exit 1
    }
    
    echo ""
    echo -e "${GREEN}✓ Migraciones aplicadas correctamente${NC}"
else
    echo ""
    echo -e "${YELLOW}La tabla no existe. Aplicando migraciones normalmente...${NC}"
    python manage.py migrate || {
        echo -e "${RED}Error al aplicar migraciones. Revisa el error arriba.${NC}"
        exit 1
    }
fi

echo ""
echo -e "${GREEN}✓ Verificando estado final...${NC}"
python manage.py showmigrations taller | grep -E "\[.*\]" | tail -5

echo ""
echo -e "${GREEN}🎉 Proceso completado!${NC}"
echo ""
echo "Para verificar:"
echo "  python manage.py check"
echo "  python manage.py showmigrations"


