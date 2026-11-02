#!/bin/bash
# Script de verificación completa post-fix
# Ejecutar en el servidor: sudo bash scripts/verificar_fix_completo.sh

echo "=========================================="
echo "🔍 Verificación Completa Post-Fix"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# 1. X-Forwarded-Proto
echo "[1] Verificando X-Forwarded-Proto en Nginx..."
if sudo grep -q "X-Forwarded-Proto" /etc/nginx/sites-enabled/* /etc/nginx/sites-available/* 2>/dev/null; then
    echo "✅ X-Forwarded-Proto configurado"
    sudo grep "X-Forwarded-Proto" /etc/nginx/sites-enabled/* /etc/nginx/sites-available/* 2>/dev/null | head -1
else
    echo "❌ X-Forwarded-Proto NO configurado"
    ERRORS=$((ERRORS + 1))
fi

# 2. Rutas .env.systemd
echo ""
echo "[2] Verificando rutas en .env.systemd..."
ENV_FILE=$(sudo find /etc/systemd /srv /opt /var/www -name ".env.systemd" -type f 2>/dev/null | head -1)
if [ -n "$ENV_FILE" ]; then
    if sudo grep -q "STATIC_ROOT=/ruta/a" "$ENV_FILE" || sudo grep -q "MEDIA_ROOT=/ruta/a" "$ENV_FILE"; then
        echo "❌ Rutas placeholder encontradas en $ENV_FILE"
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ Rutas configuradas correctamente"
        sudo grep -E "^(STATIC_ROOT|MEDIA_ROOT)=" "$ENV_FILE" 2>/dev/null || echo "  (variables no encontradas)"
    fi
else
    echo "⚠️  No se encontró .env.systemd"
    WARNINGS=$((WARNINGS + 1))
fi

# 3. Directorios
echo ""
echo "[3] Verificando directorios..."
STATIC_DIR="/srv/egarage/staticfiles"
MEDIA_DIR="/srv/egarage/media"

# Intentar detectar desde .env si existe
if [ -n "$ENV_FILE" ]; then
    DETECTED_STATIC=$(sudo grep "^STATIC_ROOT=" "$ENV_FILE" 2>/dev/null | cut -d= -f2)
    DETECTED_MEDIA=$(sudo grep "^MEDIA_ROOT=" "$ENV_FILE" 2>/dev/null | cut -d= -f2)
    if [ -n "$DETECTED_STATIC" ]; then
        STATIC_DIR="$DETECTED_STATIC"
    fi
    if [ -n "$DETECTED_MEDIA" ]; then
        MEDIA_DIR="$DETECTED_MEDIA"
    fi
fi

if [ -d "$STATIC_DIR" ] && [ -d "$MEDIA_DIR" ]; then
    echo "✅ Directorios existen"
    echo "   STATIC: $STATIC_DIR"
    echo "   MEDIA: $MEDIA_DIR"
    ls -ld "$STATIC_DIR" "$MEDIA_DIR" 2>/dev/null | awk '{print "   " $0}'
else
    echo "❌ Directorios no encontrados"
    [ ! -d "$STATIC_DIR" ] && echo "   ❌ Falta: $STATIC_DIR"
    [ ! -d "$MEDIA_DIR" ] && echo "   ❌ Falta: $MEDIA_DIR"
    ERRORS=$((ERRORS + 1))
fi

# 4. Servicio
echo ""
echo "[4] Verificando servicio egarage-gunicorn..."
if sudo systemctl is-active --quiet egarage-gunicorn; then
    echo "✅ Servicio activo"
    sudo systemctl status egarage-gunicorn --no-pager -l | head -3 | tail -1
else
    echo "❌ Servicio inactivo"
    ERRORS=$((ERRORS + 1))
fi

# 5. Test HTTP
echo ""
echo "[5] Probando sitio web..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://egarage.cl/accounts/login/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Sitio responde correctamente (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "⚠️  Redirección detectada (HTTP $HTTP_CODE)"
    echo "   Esto puede ser normal si es redirect a login, pero verifica que no sea un loop"
    WARNINGS=$((WARNINGS + 1))
elif [ "$HTTP_CODE" = "000" ]; then
    echo "⚠️  No se pudo conectar al sitio"
    WARNINGS=$((WARNINGS + 1))
else
    echo "❌ Error HTTP $HTTP_CODE"
    ERRORS=$((ERRORS + 1))
fi

# 6. Verificar logs recientes
echo ""
echo "[6] Verificando logs recientes..."
NGINX_ERRORS=$(sudo tail -n 20 /var/log/nginx/error.log 2>/dev/null | grep -i "error\|critical" | wc -l)
GUNICORN_ERRORS=$(sudo journalctl -u egarage-gunicorn -n 20 --no-pager 2>/dev/null | grep -i "error\|critical\|traceback" | wc -l)

if [ "$NGINX_ERRORS" -gt 0 ]; then
    echo "⚠️  Se encontraron $NGINX_ERRORS errores en logs de Nginx (últimas 20 líneas)"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ Sin errores críticos en logs de Nginx"
fi

if [ "$GUNICORN_ERRORS" -gt 0 ]; then
    echo "⚠️  Se encontraron $GUNICORN_ERRORS errores en logs de Gunicorn (últimas 20 líneas)"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ Sin errores críticos en logs de Gunicorn"
fi

# 7. Verificar configuración de Django
echo ""
echo "[7] Verificando configuración de Django..."
if [ -d "/srv/egarage" ]; then
    PROJECT_DIR="/srv/egarage"
elif [ -d "/opt/egarage" ]; then
    PROJECT_DIR="/opt/egarage"
else
    PROJECT_DIR=""
fi

if [ -n "$PROJECT_DIR" ] && [ -f "$PROJECT_DIR/manage.py" ]; then
    cd "$PROJECT_DIR"
    if [ -d "venv" ]; then
        source venv/bin/activate 2>/dev/null || true
    fi
    
    SECURE_PROXY=$(python manage.py shell -c "from django.conf import settings; print(settings.SECURE_PROXY_SSL_HEADER)" 2>/dev/null || echo "")
    if echo "$SECURE_PROXY" | grep -q "X_FORWARDED_PROTO"; then
        echo "✅ SECURE_PROXY_SSL_HEADER configurado correctamente"
    else
        echo "⚠️  SECURE_PROXY_SSL_HEADER: $SECURE_PROXY"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "⚠️  No se pudo verificar configuración de Django (proyecto no encontrado)"
    WARNINGS=$((WARNINGS + 1))
fi

# Resumen
echo ""
echo "=========================================="
echo "📊 Resumen"
echo "=========================================="
echo "Errores encontrados: $ERRORS"
echo "Advertencias: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ ✅ ✅ Todo está correcto. Incidente cerrado."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Hay algunas advertencias, pero no hay errores críticos."
    exit 0
else
    echo "❌ Se encontraron errores que deben corregirse."
    echo ""
    echo "🔧 Scripts de corrección disponibles:"
    echo "   - scripts/fix_nginx_x_forwarded_proto_auto.sh"
    echo "   - scripts/fix_env_systemd_rutas.sh"
    exit 1
fi
