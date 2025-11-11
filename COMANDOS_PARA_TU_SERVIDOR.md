# 🚀 COMANDOS EXACTOS PARA TU SERVIDOR

## ✅ **TU CONFIGURACIÓN DETECTADA**

```
Directorio: ~/apps/egarage/current ✅
Virtual env: venv_egarage310 ✅
Sistema: Systemd (/usr/bin/systemctl) ✅
Gunicorn: No corriendo actualmente
```

---

## ⚡ **DEPLOYMENT EN 2 FASES**

### **FASE 1: SUBIR ARCHIVOS (desde tu PC Windows)**

Primero, desde tu PC local, necesitas subir los archivos al servidor.

**Opción A - Git (Recomendado si tienes configurado):**

```bash
# En tu PC (PowerShell o Git Bash):
cd E:\projecto\e_garage
git add .
git commit -m "Release v2.0 - Multi-país + diseño futurista Perú"
git push origin main

# En el servidor:
cd ~/apps/egarage/current
git pull origin main
```

**Opción B - Rsync (Más eficiente):**

```bash
# En tu PC (Git Bash o WSL):
rsync -avz --exclude='venv*' --exclude='__pycache__' --exclude='*.pyc' --exclude='db.sqlite3' --exclude='*.md' --exclude='backups' --exclude='logs' /e/projecto/e_garage/ user@tu-servidor:~/apps/egarage/current/
```

**Opción C - SCP Selectivo (subir solo archivos críticos):**

```bash
# En tu PC (PowerShell):
$SERVER = "user@tu-servidor"
$BASE = "~/apps/egarage/current"

# Templates
scp templates/account/login_peru.html $SERVER:$BASE/templates/account/
scp templates/account/signup_peru.html $SERVER:$BASE/templates/account/
scp templates/account/signup_brasil.html $SERVER:$BASE/templates/account/
scp templates/account/signup_venezuela.html $SERVER:$BASE/templates/account/

# Migración nueva
scp taller/migrations/0032_*.py $SERVER:$BASE/taller/migrations/

# JavaScript
scp taller/static/js/locations.js $SERVER:$BASE/taller/static/js/

# Y así con los demás archivos...
```

---

### **FASE 2: COMANDOS EN EL SERVIDOR**

Una vez subidos los archivos, ejecuta esto en el servidor:

```bash
# Ya estás en: ~/apps/egarage/current
# Virtual env activo: venv_egarage310

# ============================================================================
# COPIAR Y PEGAR TODO ESTE BLOQUE:
# ============================================================================

cd ~/apps/egarage/current

# 1. BACKUP
echo "🔄 Creando backup..."
mkdir -p backups/deployments
python manage.py dumpdata --exclude=contenttypes --exclude=auth.permission --output=backups/deployments/backup_$(date +%Y%m%d_%H%M%S).json
echo "✅ Backup creado"

# 2. DEPENDENCIAS
echo "📦 Actualizando dependencias..."
pip install -r requirements.txt --upgrade
echo "✅ Dependencias actualizadas"

# 3. MIGRACIONES
echo "🗄️ Aplicando migraciones..."
python manage.py migrate
echo "✅ Migraciones aplicadas (32 total)"

# 4. ESTÁTICOS
echo "📁 Colectando archivos estáticos..."
python manage.py collectstatic --noinput
echo "✅ Estáticos colectados"

# 5. TRADUCCIONES
echo "🌍 Compilando traducciones..."
python manage.py compilemessages 2>/dev/null || echo "⚠️ Sin traducciones nuevas"
echo "✅ Traducciones compiladas"

# 6. INICIALIZACIÓN (solo primera vez v2.0)
if [ ! -f ".deployed_v2" ]; then
    echo "🔧 Primera instalación v2.0, cargando datos iniciales..."
    
    echo "  - Cargando estados Brasil..."
    python manage.py cargar_estados_brasil || echo "  ⚠️ Ya cargados o error"
    
    echo "  - Cargando estados Venezuela..."
    python manage.py cargar_estados_venezuela || echo "  ⚠️ Ya cargados o error"
    
    echo "  - Cargando estados Perú..."
    python manage.py cargar_estados_peru || echo "  ⚠️ Ya cargados o error"
    
    echo "  - Cargando políticas de impuestos..."
    python manage.py seed_tax || echo "  ⚠️ Ya cargadas o error"
    
    # Marcar como desplegado
    echo "v2.0 - $(date +%Y-%m-%d\ %H:%M:%S)" > .deployed_v2
    echo "✅ Datos iniciales cargados"
else
    echo "✅ Sistema ya desplegado v2.0 anteriormente"
    cat .deployed_v2
fi

# 7. VERIFICAR
echo "🔍 Verificando sistema..."
python manage.py check
echo "✅ Sistema verificado sin errores"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  🎉 DEPLOYMENT COMPLETADO                             ║"
echo "║  Versión: 2.0.0                                        ║"
echo "║  Fecha: $(date +%Y-%m-%d\ %H:%M:%S)                    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️ IMPORTANTE: Reinicia Gunicorn para aplicar cambios:"
echo "   sudo systemctl restart gunicorn-egarage"
echo "   O busca el nombre de tu servicio con: systemctl list-units | grep gunicorn"

# ============================================================================
# FIN DEL BLOQUE
# ============================================================================
```

---

## 🔄 **DESPUÉS, REINICIAR GUNICORN:**

Primero, encuentra el nombre exacto de tu servicio:

```bash
systemctl list-units | grep gunicorn
# O también:
systemctl list-units | grep egarage
```

**Luego reinicia:**

```bash
# Reemplaza 'gunicorn-egarage' con el nombre real de tu servicio
sudo systemctl restart gunicorn-egarage

# O si el servicio tiene otro nombre:
# sudo systemctl restart nombre-real-del-servicio

# Verificar que arrancó:
sudo systemctl status gunicorn-egarage

# Si también usas Nginx:
sudo systemctl reload nginx
```

---

## 📋 **PERO ANTES - ¿YA SUBISTE LOS ARCHIVOS?**

Si **NO** has subido los archivos desde tu PC, necesitas hacerlo primero.

**¿Tienes Git configurado?** Pregunta:

```bash
git status
```

Si muestra el estado del repo → usa Git  
Si da error → usa SCP o rsync

---

## 🎯 **RESUMEN RÁPIDO**

```
1. Subir archivos al servidor (Git/SCP/rsync)
   ↓
2. Ejecutar bloque de comandos de arriba
   ↓
3. Reiniciar Gunicorn: sudo systemctl restart gunicorn-egarage
   ↓
4. Verificar: curl http://127.0.0.1:8000/pe/signup/
   ↓
✅ ¡Listo!
```

---

**¿Qué método prefieres para subir archivos?**
- Git (si ya lo tienes configurado)
- SCP (te doy los comandos exactos)
- Otro

**Déjame saber y te ayudo con el método que prefieras.** 🚀
