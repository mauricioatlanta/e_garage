# 🚀 DEPLOYMENT EN TU SERVIDOR - eGarage v2.0

## 📍 **TU CONFIGURACIÓN DETECTADA**

**Directorio actual:** `~/apps/egarage/current`  
**Virtual env:** `venv_egarage310`  
**Branch:** `main`  
**Estado:** Ya estás en el servidor ✅

---

## ⚡ **DEPLOYMENT ADAPTADO A TU SERVIDOR**

### **PASO 1: Verificar Ubicación** ✅

```bash
# Ya estás aquí:
pwd
# Output: ~/apps/egarage/current

# Listar archivos
ls -la
```

---

### **PASO 2: Subir Archivos Nuevos**

Desde tu máquina local (Windows), subir los archivos al servidor:

```bash
# Opción A: SCP desde tu PC local (ejecutar en PowerShell/CMD)
scp deploy.sh user@servidor:~/apps/egarage/current/
scp CONFIGURACION_PRODUCCION.env.example user@servidor:~/apps/egarage/current/
scp -r templates/account/* user@servidor:~/apps/egarage/current/templates/account/
scp -r taller/migrations/* user@servidor:~/apps/egarage/current/taller/migrations/
scp -r taller/static/js/locations.js user@servidor:~/apps/egarage/current/taller/static/js/

# Opción B: Git (si tienes repo)
# En tu PC: git push origin main
# En servidor: git pull origin main

# Opción C: Copiar manualmente con editor/FTP
# Subir archivos usando FileZilla, WinSCP, etc.
```

---

### **PASO 3: Adaptar Script de Deployment**

Ya que tu servidor usa una estructura diferente, aquí está el script adaptado:

**Ejecutar en el servidor:**

```bash
# Ir a tu directorio
cd ~/apps/egarage/current

# Activar virtual environment (ya lo tienes activo)
source ~/venv_egarage310/bin/activate

# Crear backup
echo "🔄 Creando backup..."
mkdir -p backups/deployments
python manage.py dumpdata \
    --natural-foreign \
    --natural-primary \
    --exclude=contenttypes \
    --exclude=auth.permission \
    --output=backups/deployments/backup_$(date +%Y%m%d_%H%M%S).json

# Actualizar dependencias
echo "📦 Actualizando dependencias..."
pip install -r requirements.txt --upgrade

# Aplicar migraciones
echo "🗄️ Aplicando migraciones..."
python manage.py migrate

# Colectar estáticos
echo "📁 Colectando archivos estáticos..."
python manage.py collectstatic --noinput

# Compilar traducciones
echo "🌍 Compilando traducciones..."
python manage.py compilemessages

# Comandos de inicialización (solo primera vez)
if [ ! -f ".deployed_v2" ]; then
    echo "🔧 Primera instalación v2.0, cargando datos iniciales..."
    
    python manage.py cargar_estados_brasil || echo "⚠️ Estados Brasil ya cargados"
    python manage.py cargar_estados_venezuela || echo "⚠️ Estados Venezuela ya cargados"
    python manage.py cargar_estados_peru || echo "⚠️ Estados Perú ya cargados"
    python manage.py seed_tax || echo "⚠️ Tax policies ya cargadas"
    
    # Marcar como desplegado
    echo "v2.0 - $(date +%Y-%m-%d\ %H:%M:%S)" > .deployed_v2
fi

# Reiniciar servicios (adaptar según tu configuración)
echo "🔄 Reiniciando servicios..."
# Si usas Gunicorn con systemd:
# sudo systemctl restart gunicorn-egarage

# Si usas supervisor:
# sudo supervisorctl restart egarage

# Si es Render/Heroku/PaaS:
# El reinicio es automático

# Verificación
echo "✅ Verificando sistema..."
python manage.py check

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  🎉 DEPLOYMENT COMPLETADO                             ║"
echo "║  Versión: 2.0.0                                        ║"
echo "║  Fecha: $(date +%Y-%m-%d\ %H:%M:%S)                    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
```

---

## 📝 **INSTRUCCIONES DETALLADAS PARA TU SERVIDOR**

### **1. Subir Archivos Críticos (desde tu PC):**

**Archivos que DEBES subir:**

```
PRIORITARIOS:
✅ templates/account/login_peru.html           (rediseñado)
✅ templates/account/signup_peru.html          (rediseñado)
✅ templates/account/signup_brasil.html        (nuevo)
✅ templates/account/signup_venezuela.html     (actualizado)

✅ taller/migrations/0032_remove_partprice_*.py (nueva migración)

✅ taller/static/js/locations.js               (v2.0)

✅ taller/urls_extra/brasil.py                 (actualizado)
✅ taller/urls_extra/venezuela.py
✅ taller/urls_extra/peru.py

✅ taller/models/ubicacion.py                  (actualizado)
✅ taller/models/catalogo_repuestos.py
✅ taller/models/catalogo_servicios.py
✅ taller/models/clientes.py                   (actualizado)

✅ taller/management/commands/
   ├── cargar_estados_brasil.py
   ├── cargar_estados_venezuela.py
   ├── cargar_estados_peru.py
   ├── seed_tax.py
   ├── backfill_addresses.py
   └── verify_backfill.py

✅ taller/utils/validators.py                  (nuevo)

✅ taller/impuestos/engine.py
✅ taller/documentos/services.py

✅ taller/ubicacion/api.py                     (nuevo)
✅ taller/ubicacion/urls.py                    (nuevo)
```

---

### **2. Comandos en el Servidor:**

```bash
# Ya estás en: ~/apps/egarage/current
# Virtual env ya activo: venv_egarage310

# A. Backup
mkdir -p backups/deployments
python manage.py dumpdata \
    --exclude=contenttypes \
    --exclude=auth.permission \
    --output=backups/deployments/backup_$(date +%Y%m%d_%H%M%S).json

# B. Instalar dependencias (si hay nuevas)
pip install -r requirements.txt --upgrade

# C. Aplicar migraciones
python manage.py migrate

# D. Colectar estáticos
python manage.py collectstatic --noinput

# E. Compilar traducciones
python manage.py compilemessages

# F. Comandos iniciales (solo primera vez v2.0)
python manage.py cargar_estados_brasil
python manage.py cargar_estados_venezuela
python manage.py cargar_estados_peru
python manage.py seed_tax

# G. Verificar
python manage.py check

# H. Reiniciar servicios (según tu config)
# Ajustar según cómo esté configurado tu servidor
```

---

### **3. Reiniciar Servicios:**

Depende de cómo tengas configurado el servidor. Opciones comunes:

```bash
# Opción A: Systemd
sudo systemctl restart gunicorn-egarage
sudo systemctl reload nginx

# Opción B: Supervisor
sudo supervisorctl restart egarage

# Opción C: PM2
pm2 restart egarage

# Opción D: Render/Heroku (PaaS)
# No hacer nada, se reinicia automáticamente

# Opción E: Manual
pkill -f gunicorn
gunicorn gestion_taller.wsgi:application -c gunicorn_config.py &
```

**¿Cuál usas?** Verifica con:
```bash
which systemctl
which supervisorctl
which pm2
```

---

## 📦 **MÉTODO RÁPIDO - Copiar y Pegar**

**En el servidor (copiar todo esto):**

```bash
cd ~/apps/egarage/current

# Backup
mkdir -p backups/deployments
python manage.py dumpdata --exclude=contenttypes --exclude=auth.permission --output=backups/deployments/backup_$(date +%Y%m%d_%H%M%S).json

# Actualizar
pip install -r requirements.txt --upgrade
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py compilemessages

# Inicialización (solo primera vez)
if [ ! -f ".deployed_v2" ]; then
    python manage.py cargar_estados_brasil
    python manage.py cargar_estados_venezuela
    python manage.py cargar_estados_peru
    python manage.py seed_tax
    echo "v2.0 - $(date)" > .deployed_v2
fi

# Verificar
python manage.py check

echo "✅ Deployment completado. Reinicia los servicios según tu configuración."
```

---

## 🔍 **VERIFICAR QUE FUNCIONE**

```bash
# En el servidor:
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/pe/login/
curl http://127.0.0.1:8000/pe/signup/

# Desde navegador:
https://tu-dominio.com/pe/login/   (diseño futurista)
https://tu-dominio.com/pe/signup/  (4 planes)
https://tu-dominio.com/br/signup/  (portugués)
```

---

## ⚠️ **IMPORTANTE**

Antes de ejecutar los comandos, asegúrate de:

1. ✅ **Tener backup** (el script lo hace automáticamente)
2. ✅ **Archivos subidos** al servidor en `~/apps/egarage/current`
3. ✅ **Virtual env activo** (ya lo tienes: `venv_egarage310`)
4. ✅ **Base de datos PostgreSQL** funcionando

---

## 📊 **ESTRUCTURA DE TU SERVIDOR**

```
~/apps/egarage/current/          ← Tu directorio actual
├── gestion_taller/
├── taller/
├── ubicacion/
├── templates/
├── static/
├── manage.py
├── requirements.txt
├── venv_egarage310/             ← Tu virtual env (en ~/)
├── backups/                     (crear si no existe)
└── .deployed_v2                 (se creará)
```

---

## 🎊 **RESUMEN**

```
UBICACIÓN: ~/apps/egarage/current ✅
VENV: venv_egarage310 ✅
COMANDO: Copiar y pegar el bloque de arriba ✅
TIEMPO: 15-20 minutos ✅
RIESGO: Bajo (backup automático) ✅
```

---

**¿Qué hacer ahora?**

1. Subir los archivos al servidor (SCP, Git, FTP)
2. Ejecutar el bloque de comandos de arriba
3. Reiniciar servicios según tu configuración

**¿Necesitas ayuda para subir archivos o reiniciar servicios?** 

Déjame saber cómo está configurado tu servidor (systemd, supervisor, pm2, etc.) para adaptar las instrucciones de reinicio.

🚀

