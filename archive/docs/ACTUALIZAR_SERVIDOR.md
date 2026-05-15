# 🚀 Guía para Actualizar Cambios al Servidor

## Opción 1: Si usas Render.com (Deployment Automático)

Render se actualiza automáticamente cuando haces push a Git.

### Pasos:

1. **Verificar cambios locales:**
   ```powershell
   git status
   ```

2. **Agregar cambios:**
   ```powershell
   git add .
   ```

3. **Hacer commit:**
   ```powershell
   git commit -m "fix: mostrar títulos de botones en móviles"
   ```

4. **Push a GitHub:**
   ```powershell
   git push origin main
   # o si estás en otra rama:
   git push origin tu-rama
   ```

5. **Render se actualizará automáticamente** (puede tardar 2-5 minutos)

---

## Opción 2: Si usas PythonAnywhere

### Pasos:

1. **Commit y push (igual que arriba):**
   ```powershell
   git add .
   git commit -m "fix: mostrar títulos de botones en móviles"
   git push origin main
   ```

2. **Conectarte al servidor:**
   - Ve a tu dashboard de PythonAnywhere
   - Abre la consola Bash
   - O usa SSH: `ssh atlantareciclajes@ssh.pythonanywhere.com`

3. **En el servidor, ejecutar:**
   ```bash
   cd /home/atlantareciclajes/apps/egarage
   git pull origin main
   source ~/.virtualenvs/venv_egarage310/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

4. **Reiniciar la aplicación:**
   - Ve al dashboard de PythonAnywhere
   - Haz clic en "Reload" en la sección Web

---

## Opción 3: Si usas un servidor propio (VPS/Cloud)

### Usando el script automatizado:

```powershell
# Desde Windows, ejecutar:
bash scripts/deploy_to_server.sh
```

### Manualmente:

1. **Commit y push:**
   ```powershell
   git add .
   git commit -m "fix: mostrar títulos de botones en móviles"
   git push origin main
   ```

2. **Conectarte al servidor:**
   ```bash
   ssh usuario@tu-servidor.com
   ```

3. **En el servidor:**
   ```bash
   cd /opt/egarage  # o la ruta de tu proyecto
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   sudo systemctl restart egarage  # o el nombre de tu servicio
   ```

---

## ⚠️ Importante: Limpiar caché de templates

Después de actualizar, es recomendable limpiar la caché de templates:

```bash
# En el servidor:
python scripts/clear_template_cache.py
```

O manualmente:
```bash
find . -type d -name "__pycache__" -exec rm -r {} +
find . -name "*.pyc" -delete
```

---

## ✅ Verificación Post-Deploy

1. **Verificar que el sitio carga:**
   - Abre tu sitio en el navegador
   - Verifica que los botones muestran títulos en móviles

2. **Probar en móvil:**
   - Abre el sitio en un celular
   - Verifica que los botones de navegación muestran:
     - ⚙️ SETTINGS
     - 👥 CLIENTS
     - 🚗 VEHICLES
     - 🛠️ SERVICES
     - 🔧 PARTS
     - 🚪 LOGOUT
     - etc.

3. **Verificar logs (si hay problemas):**
   ```bash
   # En Render: ve a la pestaña Logs
   # En PythonAnywhere: ve a Error log en el dashboard
   # En servidor propio:
   sudo journalctl -u egarage -f
   ```

---

## 🔄 Rollback (si algo sale mal)

Si necesitas volver a la versión anterior:

```bash
# Ver commits recientes
git log --oneline -5

# Volver al commit anterior
git revert HEAD
git push origin main

# O volver a un commit específico
git reset --hard COMMIT_HASH
git push origin main --force
```

---

## 📝 Notas

- **Templates**: Los cambios en templates se reflejan inmediatamente (no necesitan migración)
- **CSS/JS**: Si cambias archivos estáticos, ejecuta `collectstatic`
- **Base de datos**: Solo ejecuta `migrate` si hay cambios en modelos
- **Tiempo de actualización**: 
  - Render: 2-5 minutos
  - PythonAnywhere: Inmediato después de reload
  - Servidor propio: Inmediato después de restart







