#!/bin/bash
# Script para aplicar botones mejorados completos
# Copia el archivo completo desde la versión local mejorada

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Aplicando mejoras completas en botones de países..."

# Backup
cp templates/public/selector_pais.html templates/public/selector_pais.html.backup_$(date +%Y%m%d_%H%M%S)

echo ""
echo "⚠️  IMPORTANTE: Este script necesita el archivo completo actualizado."
echo "   Si tienes el archivo local mejorado, cópialo manualmente o usa:"
echo "   scp templates/public/selector_pais.html usuario@servidor:/ruta/al/archivo"
echo ""
echo "   O ejecuta el script APLICAR_DISENO_METALICO_COMPLETO_SERVIDOR.sh que ya tiene"
echo "   el contenido completo embebido."
echo ""
echo "✅ Para aplicar cambios básicos de tamaño, ejecuta:"
echo "   bash APLICAR_BOTONES_MEJORADOS_SERVIDOR.sh"



