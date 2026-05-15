# 🔄 REINICIAR GUNICORN SIN SUDO

## ✅ ESTADO ACTUAL

- ✅ `collectstatic` ejecutado correctamente (646 archivos ya estaban recopilados)
- ❌ `sudo` no disponible en este servidor
- ⚠️ Necesitas reiniciar Gunicorn de otra forma

---

## 🔧 OPCIONES PARA REINICIAR GUNICORN

### Opción 1: Reiniciar con systemctl (sin sudo, si tienes permisos)

```bash
# Intentar sin sudo
systemctl restart gunicorn

# Verificar estado
systemctl status gunicorn
```

### Opción 2: Usar supervisorctl (si Gunicorn está en Supervisor)

```bash
# Verificar si Supervisor está instalado
which supervisorctl

# Si está disponible, reiniciar
supervisorctl restart gunicorn

# O si el proceso tiene otro nombre
supervisorctl status
supervisorctl restart all
```

### Opción 3: Reiniciar manualmente (matar y reiniciar proceso)

```bash
# 1. Encontrar el proceso de Gunicorn
ps aux | grep gunicorn

# 2. Ver el PID (número en la segunda columna)
# Ejemplo: atlantareciclajes  12345  ... gunicorn ...

# 3. Matar el proceso (reemplaza 12345 con el PID real)
kill -HUP 12345

# O si no funciona:
kill 12345

# 4. Reiniciar Gunicorn (depende de cómo lo tengas configurado)
# Si usas un script de inicio:
./start_gunicorn.sh

# O si lo ejecutas directamente:
gunicorn gestion_taller.wsgi:application --bind 0.0.0.0:8000
```

### Opción 4: Usar screen/tmux (si Gunicorn está corriendo en una sesión)

```bash
# Ver sesiones de screen
screen -ls

# Ver sesiones de tmux
tmux ls

# Si encuentras una sesión, conectarte y reiniciar
screen -r nombre_sesion
# o
tmux attach -t nombre_sesion
```

### Opción 5: Contactar al administrador del servidor

Si no tienes permisos para reiniciar, contacta al administrador del servidor para que reinicie Gunicorn.

---

## 🔍 DIAGNÓSTICO: Cómo está corriendo Gunicorn

Ejecuta estos comandos para entender cómo está configurado:

```bash
# 1. Ver procesos de Gunicorn corriendo
ps aux | grep gunicorn

# 2. Ver si hay un servicio systemd
systemctl list-units | grep gunicorn

# 3. Ver si Supervisor está corriendo
supervisorctl status 2>/dev/null || echo "Supervisor no disponible"

# 4. Ver archivos de configuración
ls -la /etc/systemd/system/ | grep gunicorn
ls -la /etc/supervisor/conf.d/ | grep gunicorn

# 5. Ver si hay un script de inicio
find . -name "*gunicorn*" -type f
find ~ -name "*gunicorn*" -type f 2>/dev/null
```

---

## 📋 COMANDOS RÁPIDOS (COPIA Y PEGA)

```bash
# Ver cómo está corriendo Gunicorn
ps aux | grep gunicorn | grep -v grep

# Intentar reiniciar con systemctl (sin sudo)
systemctl restart gunicorn 2>&1

# Si falla, intentar con supervisorctl
supervisorctl restart gunicorn 2>&1

# Si falla, ver el PID y reiniciar manualmente
PID=$(ps aux | grep '[g]unicorn' | awk '{print $2}' | head -1)
if [ ! -z "$PID" ]; then
    echo "PID encontrado: $PID"
    kill -HUP $PID
    echo "Señal HUP enviada al proceso"
else
    echo "No se encontró proceso de Gunicorn"
fi
```

---

## ✅ VERIFICACIÓN POST-REINICIO

Después de reiniciar, verifica:

```bash
# 1. Ver que Gunicorn está corriendo
ps aux | grep gunicorn | grep -v grep

# 2. Ver logs (si están disponibles)
tail -f /var/log/gunicorn/error.log 2>/dev/null
# o
journalctl -u gunicorn -n 20 --no-pager 2>/dev/null

# 3. Probar que la aplicación responde
curl -I http://localhost:8000 2>/dev/null || echo "Verifica la URL de tu aplicación"
```

---

## 🎯 LO MÁS IMPORTANTE

**Los archivos ya están actualizados en el servidor** (collectstatic funcionó).

**Solo necesitas reiniciar Gunicorn** para que cargue los nuevos archivos Python.

Si no puedes reiniciar ahora mismo, los cambios se aplicarán la próxima vez que se reinicie Gunicorn (automáticamente o manualmente).

---

## 🆘 SI NADA FUNCIONA

1. **Verifica que los archivos se subieron correctamente:**
   ```bash
   ls -la templates/taller/common/documentos/document_form.html
   ls -la templates/cl/es/vehiculos/crear.html
   ls -la taller/vehiculos/views_country_aware.py
   ls -la taller/documentos/views_migrated.py
   ```

2. **Verifica las fechas de modificación:**
   ```bash
   stat templates/taller/common/documentos/document_form.html | grep Modify
   ```

3. **Si los archivos están actualizados, los cambios se aplicarán en el próximo reinicio de Gunicorn.**

