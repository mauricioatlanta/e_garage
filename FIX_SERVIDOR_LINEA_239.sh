#!/bin/bash
# Script para corregir el error VariableDoesNotExist en document_form.html
# Ejecutar en el servidor: /home/atlantareciclajes/apps/egarage/current

FILE_PATH="/home/atlantareciclajes/apps/egarage/current/templates/taller/common/documentos/document_form.html"

echo "🔍 Verificando archivo..."
if [ ! -f "$FILE_PATH" ]; then
    echo "❌ Error: Archivo no encontrado: $FILE_PATH"
    exit 1
fi

echo "📝 Buscando líneas problemáticas..."
OLD_PATTERN="company_country|default:request.company_country|default:empresa.pais|default:'CL'"
NEW_PATTERN="empresa.pais|default:'CL'"

# Verificar si existe el patrón antiguo
if grep -q "$OLD_PATTERN" "$FILE_PATH"; then
    echo "✅ Patrón antiguo encontrado. Aplicando corrección..."
    
    # Crear backup
    BACKUP_FILE="${FILE_PATH}.backup_$(date +%Y%m%d_%H%M%S)"
    cp "$FILE_PATH" "$BACKUP_FILE"
    echo "💾 Backup creado: $BACKUP_FILE"
    
    # Reemplazar en la línea del bloque documento_title (línea ~186)
    sed -i "s/{% with active_country=company_country|default:request.company_country|default:empresa.pais|default:'CL' %}/{% with active_country=empresa.pais|default:'CL' %}/g" "$FILE_PATH"
    
    # Reemplazar en la línea del bloque documento_content (línea ~239)
    sed -i "s/{% with active_country=company_country|default:request.company_country|default:empresa.pais|default:'CL' %}/{% with active_country=empresa.pais|default:'CL' %}/g" "$FILE_PATH"
    
    echo "✅ Corrección aplicada"
    
    # Verificar que el cambio se aplicó
    if grep -q "$OLD_PATTERN" "$FILE_PATH"; then
        echo "⚠️  Advertencia: Todavía se encontró el patrón antiguo. Verificar manualmente."
        exit 1
    else
        echo "✅ Verificación: Patrón antiguo eliminado correctamente"
    fi
    
    # Verificar que el patrón nuevo está presente
    if grep -q "active_country=empresa.pais|default:'CL'" "$FILE_PATH"; then
        echo "✅ Verificación: Patrón nuevo encontrado correctamente"
        echo ""
        echo "📋 Resumen:"
        echo "   - Backup: $BACKUP_FILE"
        echo "   - Archivo corregido: $FILE_PATH"
        echo ""
        echo "🚀 Próximos pasos:"
        echo "   1. Verificar que el archivo está correcto:"
        echo "      grep -n 'active_country=empresa.pais' $FILE_PATH"
        echo "   2. Recargar la aplicación (no es necesario reiniciar, templates se recargan automáticamente)"
        echo "   3. Probar la URL: https://www.egarage.cl/us/documentos/form/"
    else
        echo "❌ Error: Patrón nuevo no encontrado después de la corrección"
        exit 1
    fi
else
    echo "ℹ️  El patrón antiguo no se encontró. El archivo puede estar ya corregido."
    echo "   Verificando patrón nuevo..."
    if grep -q "active_country=empresa.pais|default:'CL'" "$FILE_PATH"; then
        echo "✅ El archivo ya está correcto"
    else
        echo "⚠️  Advertencia: No se encontró ni el patrón antiguo ni el nuevo."
        echo "   Verificar manualmente el archivo."
    fi
fi



