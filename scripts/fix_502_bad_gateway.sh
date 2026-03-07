#!/bin/bash
# Script para diagnosticar y solucionar error 502 Bad Gateway
# Uso: sudo bash scripts/fix_502_bad_gateway.sh

set -e

echo "=========================================="
echo "🔍 DIAGNÓSTICO 502 BAD GATEWAY - egarage.cl"
echo "=========================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_status() {
    if [ "$1" = "OK" ]; then
        echo -e "${GREEN}✅ $2${NC}"
    elif [ "$1" = "ERROR" ]; then
        echo -e "${RED}❌ $2${NC}"
    elif [ "$1" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  $2${NC}"
    else
        echo "ℹ️  $2"
    fi
}

# ============================================================================
# 1. VERIFICAR SERVICIO GUNICORN
# ============================================================================
echo "1️⃣  Verificando servicio Gunicorn..."
echo "----------------------------------------"

# Buscar servicios relacionados con egarage/gunicorn
SERVICE_NAMES=("egarage" "gunicorn-egarage" "gunicorn" "egarage.service")

GUNICORN_SERVICE=""
for service in "${SERVICE_NAMES[@]}"; do
    if systemctl list-units --all | grep -q "$service"; then
        GUNICORN_SERVICE="$service"
        break
    fi
done

if [ -z "$GUNICORN_SERVICE" ]; then
    print_status "ERROR" "No se encontró servicio Gunicorn"
    echo ""
    echo "Servicios disponibles relacionados:"
    systemctl list-units --all | grep -E "(gunicorn|egarage)" || echo "Ninguno encontrado"
    echo ""
    print_status "WARN" "Necesitas crear el servicio systemd primero"
else
    print_status "OK" "Servicio encontrado: $GUNICORN_SERVICE"
    
    # Verificar estado
    if systemctl is-active --quiet "$GUNICORN_SERVICE"; then
        print_status "OK" "Servicio está ACTIVO"
    else
        print_status "ERROR" "Servicio NO está activo"
        echo ""
        echo "Estado del servicio:"
        systemctl status "$GUNICORN_SERVICE" --no-pager -l || true
        echo ""
        print_status "WARN" "Intentando iniciar el servicio..."
        systemctl start "$GUNICORN_SERVICE" || true
        sleep 2
        if systemctl is-active --quiet "$GUNICORN_SERVICE"; then
            print_status "OK" "Servicio iniciado correctamente"
        else
            print_status "ERROR" "No se pudo iniciar el servicio"
            echo ""
            echo "Últimas líneas del log:"
            journalctl -u "$GUNICORN_SERVICE" -n 20 --no-pager || true
        fi
    fi
fi

echo ""

# ============================================================================
# 2. VERIFICAR SOCKET FILE O PUERTO
# ============================================================================
echo "2️⃣  Verificando conexión Gunicorn..."
echo "----------------------------------------"

# Posibles ubicaciones del socket
SOCKET_PATHS=(
    "/opt/egarage/egarage.sock"
    "/var/www/egarage/egarage.sock"
    "/srv/egarage/egarage.sock"
    "/tmp/egarage.sock"
)

SOCKET_FOUND=""
for socket_path in "${SOCKET_PATHS[@]}"; do
    if [ -S "$socket_path" ]; then
        SOCKET_FOUND="$socket_path"
        print_status "OK" "Socket encontrado: $socket_path"
        
        # Verificar permisos
        SOCKET_PERMS=$(stat -c "%a" "$socket_path" 2>/dev/null || echo "unknown")
        SOCKET_OWNER=$(stat -c "%U:%G" "$socket_path" 2>/dev/null || echo "unknown")
        echo "   Permisos: $SOCKET_PERMS"
        echo "   Propietario: $SOCKET_OWNER"
        
        # Verificar que nginx puede leerlo
        if [ -r "$socket_path" ]; then
            print_status "OK" "Socket es legible"
        else
            print_status "WARN" "Socket puede no ser legible por nginx"
        fi
        break
    fi
done

# Si no hay socket, verificar puerto TCP
if [ -z "$SOCKET_FOUND" ]; then
    print_status "WARN" "No se encontró socket Unix"
    echo ""
    echo "Verificando si Gunicorn está escuchando en puerto TCP..."
    
    # Verificar puertos comunes
    PORTS=(8000 8001 8002)
    PORT_FOUND=""
    for port in "${PORTS[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            PORT_FOUND="$port"
            print_status "OK" "Gunicorn escuchando en puerto $port"
            break
        fi
    done
    
    if [ -z "$PORT_FOUND" ]; then
        print_status "ERROR" "Gunicorn no está escuchando en ningún puerto conocido"
    fi
fi

echo ""

# ============================================================================
# 3. VERIFICAR CONFIGURACIÓN NGINX
# ============================================================================
echo "3️⃣  Verificando configuración Nginx..."
echo "----------------------------------------"

# Buscar archivo de configuración
NGINX_CONFIGS=(
    "/etc/nginx/sites-enabled/egarage"
    "/etc/nginx/sites-enabled/egarage.cl"
    "/etc/nginx/sites-available/egarage"
    "/etc/nginx/sites-available/egarage.cl"
    "/etc/nginx/conf.d/egarage.conf"
)

NGINX_CONFIG=""
for config in "${NGINX_CONFIGS[@]}"; do
    if [ -f "$config" ]; then
        NGINX_CONFIG="$config"
        print_status "OK" "Configuración encontrada: $config"
        break
    fi
done

if [ -z "$NGINX_CONFIG" ]; then
    print_status "ERROR" "No se encontró configuración de Nginx para egarage"
else
    # Verificar proxy_pass
    if grep -q "proxy_pass" "$NGINX_CONFIG"; then
        print_status "OK" "proxy_pass configurado"
        echo ""
        echo "Configuración proxy_pass encontrada:"
        grep -A 5 "proxy_pass" "$NGINX_CONFIG" | head -10
        echo ""
        
        # Verificar headers importantes
        if grep -q "X-Forwarded-Proto" "$NGINX_CONFIG"; then
            print_status "OK" "Header X-Forwarded-Proto configurado"
        else
            print_status "WARN" "Header X-Forwarded-Proto NO configurado (puede causar problemas)"
        fi
        
        if grep -q "X-Real-IP" "$NGINX_CONFIG"; then
            print_status "OK" "Header X-Real-IP configurado"
        else
            print_status "WARN" "Header X-Real-IP NO configurado"
        fi
    else
        print_status "ERROR" "proxy_pass NO encontrado en configuración"
    fi
    
    # Verificar sintaxis
    if nginx -t 2>&1 | grep -q "successful"; then
        print_status "OK" "Sintaxis de Nginx es válida"
    else
        print_status "ERROR" "Error en sintaxis de Nginx"
        echo ""
        nginx -t
    fi
fi

echo ""

# ============================================================================
# 4. VERIFICAR LOGS DE ERROR
# ============================================================================
echo "4️⃣  Revisando logs de error..."
echo "----------------------------------------"

# Logs de Nginx
NGINX_ERROR_LOG="/var/log/nginx/error.log"
if [ -f "$NGINX_ERROR_LOG" ]; then
    print_status "OK" "Revisando log de errores de Nginx..."
    echo ""
    echo "Últimas 10 líneas del error log:"
    tail -10 "$NGINX_ERROR_LOG" | grep -i "502\|bad gateway\|connect\|upstream" || echo "No se encontraron errores 502 recientes"
    echo ""
fi

# Logs específicos de egarage
EGARAGE_ERROR_LOG="/var/log/nginx/egarage_error.log"
if [ -f "$EGARAGE_ERROR_LOG" ]; then
    print_status "OK" "Revisando log específico de egarage..."
    echo ""
    tail -10 "$EGARAGE_ERROR_LOG" | grep -i "502\|bad gateway\|connect\|upstream" || echo "No se encontraron errores 502 recientes"
    echo ""
fi

# Logs de Gunicorn
if [ -n "$GUNICORN_SERVICE" ]; then
    print_status "OK" "Revisando logs de Gunicorn..."
    echo ""
    journalctl -u "$GUNICORN_SERVICE" -n 20 --no-pager | tail -20
    echo ""
fi

# ============================================================================
# 5. SOLUCIONES SUGERIDAS
# ============================================================================
echo "=========================================="
echo "🔧 SOLUCIONES SUGERIDAS"
echo "=========================================="
echo ""

if [ -z "$GUNICORN_SERVICE" ] || ! systemctl is-active --quiet "$GUNICORN_SERVICE" 2>/dev/null; then
    echo "1. INICIAR SERVICIO GUNICORN:"
    if [ -n "$GUNICORN_SERVICE" ]; then
        echo "   sudo systemctl start $GUNICORN_SERVICE"
        echo "   sudo systemctl enable $GUNICORN_SERVICE  # Para iniciar automáticamente"
    else
        echo "   Primero necesitas crear el servicio systemd"
        echo "   Ver: scripts/deployment_guide.py"
    fi
    echo ""
fi

if [ -z "$SOCKET_FOUND" ] && [ -z "$PORT_FOUND" ]; then
    echo "2. VERIFICAR QUE GUNICORN ESTÁ CORRIENDO:"
    echo "   ps aux | grep gunicorn"
    echo "   netstat -tuln | grep 8000  # O el puerto configurado"
    echo ""
fi

if [ -n "$SOCKET_FOUND" ]; then
    SOCKET_DIR=$(dirname "$SOCKET_FOUND")
    SOCKET_FILE=$(basename "$SOCKET_FOUND")
    echo "3. VERIFICAR PERMISOS DEL SOCKET:"
    echo "   sudo chmod 666 $SOCKET_FOUND"
    echo "   # O agregar nginx al grupo del socket:"
    echo "   sudo usermod -a -G $(stat -c '%G' $SOCKET_FOUND) nginx"
    echo ""
fi

echo "4. REINICIAR SERVICIOS:"
if [ -n "$GUNICORN_SERVICE" ]; then
    echo "   sudo systemctl restart $GUNICORN_SERVICE"
fi
echo "   sudo systemctl reload nginx"
echo ""

echo "5. VERIFICAR CONEXIÓN:"
if [ -n "$SOCKET_FOUND" ]; then
    echo "   curl --unix-socket $SOCKET_FOUND http://localhost/health/ || echo 'Error conectando'"
elif [ -n "$PORT_FOUND" ]; then
    echo "   curl http://localhost:$PORT_FOUND/health/ || echo 'Error conectando'"
fi
echo ""

echo "6. VERIFICAR LOGS EN TIEMPO REAL:"
echo "   sudo tail -f /var/log/nginx/error.log"
if [ -n "$GUNICORN_SERVICE" ]; then
    echo "   sudo journalctl -u $GUNICORN_SERVICE -f"
fi
echo ""

# ============================================================================
# 6. INTENTAR SOLUCIÓN AUTOMÁTICA
# ============================================================================
echo "=========================================="
echo "🚀 INTENTAR SOLUCIÓN AUTOMÁTICA"
echo "=========================================="
echo ""

read -p "¿Deseas intentar solucionar automáticamente? (s/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    print_status "OK" "Aplicando soluciones automáticas..."
    echo ""
    
    # Reiniciar Gunicorn si existe
    if [ -n "$GUNICORN_SERVICE" ]; then
        print_status "OK" "Reiniciando $GUNICORN_SERVICE..."
        systemctl restart "$GUNICORN_SERVICE" || print_status "ERROR" "No se pudo reiniciar"
        sleep 2
        
        if systemctl is-active --quiet "$GUNICORN_SERVICE"; then
            print_status "OK" "Servicio reiniciado correctamente"
        else
            print_status "ERROR" "El servicio no está activo después del reinicio"
        fi
    fi
    
    # Arreglar permisos del socket si existe
    if [ -n "$SOCKET_FOUND" ]; then
        print_status "OK" "Ajustando permisos del socket..."
        chmod 666 "$SOCKET_FOUND" 2>/dev/null || print_status "WARN" "No se pudieron cambiar permisos (puede requerir ajuste manual)"
    fi
    
    # Recargar Nginx
    print_status "OK" "Verificando configuración de Nginx..."
    if nginx -t 2>&1 | grep -q "successful"; then
        print_status "OK" "Sintaxis de Nginx es válida"
        print_status "OK" "Recargando Nginx..."
        systemctl reload nginx
        if [ $? -eq 0 ]; then
            print_status "OK" "Nginx recargado correctamente"
        else
            print_status "ERROR" "Error al recargar Nginx"
        fi
    else
        print_status "ERROR" "Error en configuración de Nginx, no se recargó"
        echo ""
        echo "Errores encontrados:"
        nginx -t
        echo ""
        print_status "WARN" "Corrige los errores antes de recargar Nginx"
    fi
    
    echo ""
    print_status "OK" "Soluciones aplicadas. Verifica el sitio web ahora."
    echo ""
    echo "Si el problema persiste, revisa los logs:"
    echo "  sudo tail -f /var/log/nginx/error.log"
fi

echo ""
echo "=========================================="
echo "✅ DIAGNÓSTICO COMPLETADO"
echo "=========================================="
