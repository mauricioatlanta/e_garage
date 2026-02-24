# 🚀 INICIAR/REINICIAR GUNICORN EN SERVIDOR SIN SYSTEMD

## 🔍 DIAGNÓSTICO ACTUAL

- ❌ No hay systemd (servidor compartido o Docker)
- ❌ No hay supervisor
- ❌ Gunicorn no está corriendo actualmente
- ✅ Los archivos están actualizados

---

## 🔧 OPCIONES PARA INICIAR GUNICORN

### Opción 1: Buscar scripts de inicio

```bash
# Buscar scripts de inicio en el proyecto
find . -name "*start*" -o -name "*gunicorn*" -o -name "*run*" | grep -E "\.(sh|py)$"

# Buscar en el directorio home
find ~ -name "*gunicorn*" -type f 2>/dev/null | head -10

# Ver si hay un archivo de configuración
ls -la | grep -E "gunicorn|start|run"
```

### Opción 2: Iniciar Gunicorn manualmente

```bash
# 1. Verificar que estás en el directorio correcto
pwd
# Debe ser: /home/atlantareciclajes/e_garage/deploy_atlantareciclajes

# 2. Activar entorno virtual (si existe)
# Buscar entorno virtual
ls -la | grep -E "venv|env|virtualenv"
# Si existe, activarlo:
# source venv/bin/activate
# o
# source env/bin/activate

# 3. Verificar que Gunicorn está instalado
python -m pip show gunicorn || pip show gunicorn

# 4. Iniciar Gunicorn manualmente
# Opción A: Comando básico
gunicorn gestion_taller.wsgi:application --bind 0.0.0.0:8000 --workers 3

# Opción B: Con archivo de configuración (si existe)
gunicorn -c gunicorn.conf.py gestion_taller.wsgi:application

# Opción C: En background
nohup gunicorn gestion_taller.wsgi:application --bind 0.0.0.0:8000 --workers 3 > gunicorn.log 2>&1 &
```

### Opción 3: Verificar si hay un panel de control (cPanel, Plesk, etc.)

Si estás en un servidor compartido, podrías tener:
- **cPanel**: Buscar "Python App" o "Application Manager"
- **Plesk**: Buscar "Python" en el panel
- **Otro panel**: Buscar opciones de "Python" o "WSGI"

### Opción 4: Verificar si está en un contenedor Docker

```bash
# Ver si Docker está disponible
which docker
docker ps 2>/dev/null || echo "Docker no disponible"

# Si hay contenedores, ver cuáles están corriendo
docker ps
```

### Opción 5: Verificar configuración del hosting

```bash
# Ver archivos de configuración comunes
ls -la | grep -E "\.(conf|ini|yaml|yml)$"
ls -la Procfile 2>/dev/null
ls -la .platform/ 2>/dev/null
ls -la .ebextensions/ 2>/dev/null

# Ver si hay un archivo de configuración de hosting
cat Procfile 2>/dev/null
cat .platform/hooks/deploy 2>/dev/null
```

---

## 📋 COMANDOS DE DIAGNÓSTICO (EJECUTAR PRIMERO)

```bash
# 1. Ver estructura del proyecto
ls -la

# 2. Buscar archivos relacionados con Gunicorn
find . -name "*gunicorn*" -type f 2>/dev/null

# 3. Ver si hay un entorno virtual
ls -la | grep -E "venv|env|virtualenv"

# 4. Verificar Python y pip
python --version
python -m pip --version

# 5. Ver si Gunicorn está instalado
python -m pip list | grep gunicorn

# 6. Ver archivos de configuración
ls -la *.conf *.ini *.yaml *.yml 2>/dev/null
cat Procfile 2>/dev/null
```

---

## 🎯 SOLUCIÓN MÁS PROBABLE

Si estás en un servidor compartido (como cPanel, Plesk, etc.), Gunicorn probablemente se inicia automáticamente o desde el panel de control.

### Verificar archivos de configuración WSGI

```bash
# Buscar archivo wsgi.py
find . -name "wsgi.py" -type f

# Ver contenido (debería tener algo como)
cat gestion_taller/wsgi.py

# Ver si hay un archivo .htaccess o similar
ls -la .htaccess public_html/ 2>/dev/null
```

---

## ✅ VERIFICACIÓN FINAL

Después de iniciar Gunicorn (cualquiera que sea el método), verifica:

```bash
# 1. Ver que el proceso está corriendo
ps aux | grep gunicorn | grep -v grep

# 2. Ver si está escuchando en un puerto
netstat -tuln | grep -E "8000|8080|5000" || ss -tuln | grep -E "8000|8080|5000"

# 3. Probar que responde
curl -I http://localhost:8000 2>/dev/null || curl -I http://127.0.0.1:8000 2>/dev/null
```

---

## 🆘 SI NO PUEDES INICIAR GUNICORN

**Los archivos ya están actualizados en el servidor.** 

Si no puedes reiniciar Gunicorn ahora:
1. Los cambios se aplicarán cuando el servidor reinicie automáticamente
2. O cuando el administrador del servidor reinicie el servicio
3. O cuando uses el panel de control del hosting para reiniciar

**Lo importante:** Los 4 archivos modificados ya están en el servidor y funcionarán cuando Gunicorn se reinicie.

---

## 📞 CONTACTAR ADMINISTRADOR

Si no puedes iniciar/reiniciar Gunicorn, contacta al administrador del servidor o del hosting y pide que reinicien el servicio de Python/Gunicorn.

**Información para el administrador:**
- Los archivos ya están actualizados
- Solo necesita reiniciar el servicio de Gunicorn/WSGI
- No se requieren migraciones de base de datos
- No se requieren cambios de configuración

