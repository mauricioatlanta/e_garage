# 📋 Checklist de Deployment - eGarage

## ⚠️ REGLA DE ORO
**NUNCA edites código directamente en el servidor. SIEMPRE edita en tu PC y deploya.**

---

## 🔴 ANTES DEL DEPLOYMENT (Pre-Deploy Checklist)

### 1. Verificaciones Locales
- [ ] **Git está limpio**: `git status` no muestra cambios sin commitear
- [ ] **Tests pasan**: `python manage.py test` (si tienes tests)
- [ ] **No hay errores de linter**: `python manage.py check`
- [ ] **Requirements.txt actualizado**: Si instalaste paquetes nuevos
- [ ] **Migraciones creadas**: `python manage.py makemigrations --check`
- [ ] **Branch correcta**: Estás en `main` o `master`

### 2. Commit y Push
```bash
git add -A
git commit -m "Descripción clara del cambio"
git push origin main
```

### 3. Backup del Servidor (IMPORTANTE)
```bash
# Conectarte al servidor y hacer backup
ssh usuario@server
cd /home/atlantareciclajes/apps/egarage
tar -czf ~/backups/egarage_$(date +%Y%m%d_%H%M%S).tar.gz current/
```

---

## 🟢 DURANTE EL DEPLOYMENT

### Opción A: Script Automático (Recomendado)
```bash
./scripts/deploy_to_server.sh
```

### Opción B: Manual (Si el script falla)
```bash
# 1. SSH al servidor
ssh atlantareciclajes@ssh.pythonanywhere.com

# 2. Crear nueva release
cd /home/atlantareciclajes/apps/egarage
RELEASE=$(date +%Y-%m-%d_%H%M%S)
mkdir -p releases/$RELEASE
cd releases/$RELEASE

# 3. Clonar código
git clone --depth=1 git@github.com:TU-USUARIO/egarage.git .

# 4. Activar venv
source ~/.virtualenvs/venv_egarage310/bin/activate

# 5. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 6. Migraciones
python manage.py migrate

# 7. Collectstatic
python manage.py collectstatic --noinput

# 8. Verificar
python manage.py check

# 9. Actualizar current
cd /home/atlantareciclajes/apps/egarage
ln -sfn releases/$RELEASE current

# 10. Reload WSGI
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## 🔵 DESPUÉS DEL DEPLOYMENT (Post-Deploy Checklist)

### 1. Verificaciones en el Servidor
- [ ] **Sitio carga**: Abrir https://atlantareciclajes.pythonanywhere.com
- [ ] **No hay error 500**: Revisar `/var/log/` si hay errores
- [ ] **Login funciona**: Probar login con usuario de prueba
- [ ] **Funcionalidades críticas**: Probar crear cliente, vehículo, documento

### 2. Monitoreo Post-Deploy
- [ ] **Revisar logs**: `tail -f /var/log/atlantareciclajes.pythonanywhere.com.error.log`
- [ ] **Revisar métricas**: Tiempo de carga, errores 404/500
- [ ] **Notificar equipo**: Si hay otros usuarios, avisar del deployment

### 3. Rollback (Si algo sale mal)
```bash
ssh atlantareciclajes@ssh.pythonanywhere.com
cd /home/atlantareciclajes/apps/egarage
# Ver releases disponibles
ls -lt releases/
# Apuntar a release anterior
ln -sfn releases/RELEASE_ANTERIOR current
# Reload
touch /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## 🚨 PROBLEMAS COMUNES Y SOLUCIONES

### Problema: "pip install falla con timeout"
**Solución:**
```bash
pip install -r requirements.txt --timeout 300 --retries 3
```

### Problema: "ImportError después de deployment"
**Causa:** Dependencias no instaladas correctamente
**Solución:**
```bash
# Reinstalar todo desde cero
pip install --force-reinstall -r requirements.txt
```

### Problema: "Archivos estáticos no cargan (404)"
**Solución:**
```bash
python manage.py collectstatic --noinput --clear
# Verificar permisos
chmod -R 755 /home/atlantareciclajes/apps/egarage/staticfiles
```

### Problema: "Migraciones fallan"
**Solución:**
```bash
# Ver estado de migraciones
python manage.py showmigrations
# Si hay conflictos, hacer merge de migraciones
python manage.py makemigrations --merge
python manage.py migrate
```

### Problema: "Error 500 después de deployment"
**Solución:**
```bash
# 1. Ver logs
tail -n 100 /var/log/atlantareciclajes.pythonanywhere.com.error.log
# 2. Verificar settings
python manage.py check --deploy
# 3. Verificar WSGI
cat /var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py
```

---

## 📊 MÉTRICAS DE DEPLOYMENT

### Tiempo Normal
- **Deployment completo**: 3-5 minutos
- **Solo código (sin deps)**: 1-2 minutos
- **Rollback**: 30 segundos

### Cuando Requiere Más Tiempo
- **Primera instalación**: 10-15 minutos (instalar todas las deps)
- **Actualización mayor de Django**: 5-8 minutos
- **Migraciones pesadas**: Variable según tamaño BD

---

## 🎯 FLUJO IDEAL

```
PC (Desarrollo)  →  Git (GitHub/GitLab)  →  Servidor (PythonAnywhere)
     ↓                      ↓                        ↓
  git commit            git push                 git pull
  git push              (automático)          + pip install
                                              + migrate
                                              + collectstatic
                                              + reload WSGI
```

**NUNCA:** Servidor → editar → desincronización ❌
**SIEMPRE:** PC → Git → Servidor ✅

---

## 📞 En Caso de Emergencia

1. **Rollback inmediato**: Ver sección "Rollback" arriba
2. **Restaurar backup**:
   ```bash
   cd /home/atlantareciclajes/apps/egarage
   tar -xzf ~/backups/egarage_TIMESTAMP.tar.gz
   ```
3. **Contactar soporte PythonAnywhere**: https://www.pythonanywhere.com/support/

---

**Última actualización**: $(date)
**Mantenido por**: Tu equipo





