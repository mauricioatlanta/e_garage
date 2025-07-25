#!/bin/bash
# Script de configuración para el agente de notificaciones como cronjob
# Uso: bash setup_notifications_cron.sh

echo "🚀 Configurando agente de notificaciones automáticas para eGarage"

# Directorio del proyecto
PROJECT_DIR="/c/projecto/projecto_1/e_garage"
SCRIPT_PATH="$PROJECT_DIR/scripts/notification_agent.py"
LOG_PATH="$PROJECT_DIR/logs/notification_agent.log"

# Verificar que el script existe
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Error: No se encuentra el script en $SCRIPT_PATH"
    exit 1
fi

# Crear directorio de logs si no existe
mkdir -p "$PROJECT_DIR/logs"

# Configurar el cronjob
echo "📅 Configurando cronjob para ejecutar diariamente a las 9:00 AM..."

# Crear entrada de cron
CRON_ENTRY="0 9 * * * cd $PROJECT_DIR && python $SCRIPT_PATH >> $LOG_PATH 2>&1"

# Verificar si ya existe una entrada similar
if crontab -l 2>/dev/null | grep -q "notification_agent.py"; then
    echo "⚠️  Ya existe una entrada de cronjob para notification_agent.py"
    echo "📋 Entradas actuales:"
    crontab -l | grep notification_agent.py
    
    read -p "¿Deseas reemplazarla? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remover entrada existente
        crontab -l | grep -v "notification_agent.py" | crontab -
        echo "🗑️  Entrada anterior removida"
    else
        echo "❌ Cancelado"
        exit 0
    fi
fi

# Agregar nueva entrada
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cronjob configurado exitosamente!"
echo "📋 Entrada agregada: $CRON_ENTRY"

# Mostrar cronjobs actuales
echo ""
echo "📅 Cronjobs actuales:"
crontab -l

# Información adicional
echo ""
echo "ℹ️  Información adicional:"
echo "   • El agente se ejecutará todos los días a las 9:00 AM"
echo "   • Los logs se guardan en: $LOG_PATH"
echo "   • Para ver los logs: tail -f $LOG_PATH"
echo "   • Para remover: crontab -e (y eliminar la línea correspondiente)"

# Probar el script manualmente
echo ""
read -p "¿Deseas probar el script ahora? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 Ejecutando prueba..."
    cd "$PROJECT_DIR"
    python "$SCRIPT_PATH"
    echo "✅ Prueba completada. Revisa el output arriba."
fi

echo ""
echo "🎉 ¡Configuración completada!"
echo "📧 El agente enviará notificaciones automáticas de vencimientos de trials y suscripciones."
