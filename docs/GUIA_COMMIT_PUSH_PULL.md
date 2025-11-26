# 🚀 Guía: Commit, Push y Pull en el Servidor

## 📋 Proceso Completo

### Paso 1: Commit y Push (Local)

#### 1.1. Verificar cambios
```bash
git status
```

#### 1.2. Agregar archivos al staging
```bash
# Opción A: Agregar todos los archivos modificados
git add -u

# Opción B: Agregar archivos específicos
git add archivo1.py archivo2.py

# Opción C: Agregar todo (incluyendo archivos nuevos)
git add .
```

#### 1.3. Hacer commit
```bash
git commit -m "Descripción de los cambios realizados"
```

#### 1.4. Hacer push
```bash
git push origin main
```

**Nota:** Si es la primera vez o hay conflictos:
```bash
git push origin main --force  # ⚠️ Solo si es necesario
```

---

### Paso 2: Pull en el Servidor

#### 2.1. Conectarse al servidor
```bash
ssh atlantareciclajes@ssh.pythonanywhere.com
```

#### 2.2. Ir al directorio del proyecto
```bash
# Opción 1: Si el proyecto está en apps/egarage/current
cd /home/atlantareciclajes/apps/egarage/current

# Opción 2: Si el proyecto está en ~/egarage
cd ~/egarage
```

**Para encontrar la ruta exacta:**
```bash
find ~ -name "manage.py" -type f 2>/dev/null
```

#### 2.3. Activar virtualenv (si es necesario)
```bash
source ~/.virtualenvs/venv_egarage310/bin/activate
# O
workon venv_egarage
```

#### 2.4. Hacer pull
```bash
git pull origin main
```

#### 2.5. Instalar dependencias (si hay nuevas)
```bash
pip3.10 install --user -r requirements.txt
```

#### 2.6. Ejecutar migraciones
```bash
python3.10 manage.py migrate
```

#### 2.7. Recopilar archivos estáticos
```bash
python3.10 manage.py collectstatic --noinput
```

#### 2.8. Reiniciar aplicación
```bash
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## ⚡ Script Rápido (Todo en Uno)

### En tu máquina local:
```bash
# 1. Agregar cambios
git add -u

# 2. Commit
git commit -m "Actualización: [describe tus cambios]"

# 3. Push
git push origin main
```

### En el servidor (después de conectarte):
```bash
cd ~/egarage && \
git pull origin main && \
pip3.10 install --user -r requirements.txt && \
python3.10 manage.py migrate && \
python3.10 manage.py collectstatic --noinput && \
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## 🔍 Verificación Post-Actualización

### 1. Verificar que el servidor funciona:
```bash
curl -I https://www.egarage.cl/
```

### 2. Ver logs de errores:
```bash
tail -f ~/logs/user/error.log
```

---

## ⚠️ Solución de Problemas

### Error: "Your branch is ahead of 'origin/main'"
**Solución:** Ya tienes commits locales, solo necesitas hacer push:
```bash
git push origin main
```

### Error: "Updates were rejected"
**Solución:** Primero hacer pull, resolver conflictos, luego push:
```bash
git pull origin main
# Resolver conflictos si los hay
git push origin main
```

### Error: "Permission denied" en el servidor
**Solución:** Verificar permisos y ruta:
```bash
# Verificar que estás en el directorio correcto
pwd
ls -la manage.py

# Verificar permisos
ls -la .git
```

### Error: "No se encuentra manage.py" en el servidor
**Solución:** Buscar el proyecto:
```bash
find ~ -name "manage.py" -type f 2>/dev/null
cd /ruta/encontrada
```

---

## 📝 Ejemplo Completo

```bash
# ===== EN TU MÁQUINA LOCAL =====

# 1. Ver qué cambió
git status

# 2. Agregar cambios
git add taller/vehiculos/views_fbv.py
git add templates/taller/us/en/vehiculos/crear_vehiculo.html

# 3. Commit
git commit -m "Fix: Corrección en formulario de vehículos para USA"

# 4. Push
git push origin main

# ===== EN EL SERVIDOR (después de SSH) =====

# 1. Ir al proyecto
cd ~/egarage

# 2. Pull
git pull origin main

# 3. Actualizar dependencias
pip3.10 install --user -r requirements.txt

# 4. Migraciones
python3.10 manage.py migrate

# 5. Estáticos
python3.10 manage.py collectstatic --noinput

# 6. Reiniciar
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py

# 7. Verificar
curl -I https://www.egarage.cl/
```

---

## 🎯 Checklist Rápido

- [ ] `git add` - Archivos agregados
- [ ] `git commit` - Commit realizado
- [ ] `git push` - Push exitoso
- [ ] SSH al servidor
- [ ] `cd` al directorio del proyecto
- [ ] `git pull` - Pull exitoso
- [ ] `pip install` - Dependencias actualizadas
- [ ] `migrate` - Migraciones ejecutadas
- [ ] `collectstatic` - Estáticos recopilados
- [ ] `touch wsgi` - Aplicación reiniciada
- [ ] Verificación del sitio funcionando

---

**Última actualización:** Diciembre 2024

