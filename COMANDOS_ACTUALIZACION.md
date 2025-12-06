# 🚀 Comandos para Actualizar en el Servidor

## 📋 Resumen de Cambios

**Archivos nuevos:** 20+
**Archivos modificados:** 11

---

## 1️⃣ LOCAL - Preparar y Subir Cambios

```bash
# Ver todos los cambios
git status

# Agregar todos los archivos
git add .

# Hacer commit con mensaje descriptivo
git commit -m "Implementación completa: Sistema de Kilometraje, Garantías, Recordatorios, Historial Digital y Portal del Cliente

- Modelo KilometrajeRegistro para historial inmutable
- Trazabilidad de garantías con detección automática
- Recordatorios de mantenimiento predictivo
- Widget de alertas en dashboard
- Historial de mantenimiento digital
- Exportación a PDF/Excel
- Portal del cliente con autenticación por token/credenciales"

# Subir al repositorio
git push origin main
# o si tu rama es master:
# git push origin master
```

---

## 2️⃣ SERVIDOR - Actualizar Código

```bash
# Conectarse al servidor
ssh usuario@servidor

# Ir al directorio del proyecto
cd /ruta/al/proyecto/e_garage

# Actualizar código
git pull origin main
# o
git pull origin master
```

---

## 3️⃣ SERVIDOR - Migraciones

```bash
# Crear migraciones para nuevos modelos
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Verificar migraciones aplicadas
python manage.py showmigrations portal
python manage.py showmigrations taller
```

---

## 4️⃣ SERVIDOR - Dependencias

```bash
# Instalar librerías necesarias
pip install weasyprint openpyxl

# O si usas requirements.txt, actualizarlo primero y luego:
pip install -r requirements.txt
```

---

## 5️⃣ SERVIDOR - Archivos Estáticos

```bash
# Recolectar archivos estáticos
python manage.py collectstatic --noinput
```

---

## 6️⃣ SERVIDOR - Reiniciar Servicios

### Opción A: Gunicorn
```bash
sudo systemctl restart gunicorn
# o
sudo supervisorctl restart gunicorn
```

### Opción B: uWSGI
```bash
sudo systemctl restart uwsgi
# o
touch /ruta/al/proyecto/reload
```

### Opción C: Apache
```bash
sudo systemctl restart apache2
```

### Opción D: Nginx + Gunicorn
```bash
sudo systemctl restart gunicorn
sudo systemctl reload nginx
```

---

## 7️⃣ SERVIDOR - Verificar

```bash
# Verificar salud del servidor
curl http://localhost:8000/health/

# Ver logs en tiempo real
tail -f /var/log/gunicorn/error.log
```

---

## ✅ Checklist Rápido

```bash
# 1. Git pull
git pull origin main

# 2. Migraciones
python manage.py makemigrations
python manage.py migrate

# 3. Dependencias
pip install weasyprint openpyxl

# 4. Estáticos
python manage.py collectstatic --noinput

# 5. Reiniciar
sudo systemctl restart gunicorn
```

---

## 🧪 Pruebas Post-Despliegue

1. **Crear documento con kilometraje:**
   - `/cl/documentos/crear/` o `/us/documentos/crear/`
   - Ingresar kilometraje y guardar

2. **Ver historial:**
   - Ir a ficha de vehículo
   - Clic en "Ver Historial de Mantenimiento"

3. **Exportar PDF:**
   - Desde historial, clic en "Exportar PDF"

4. **Portal del cliente:**
   - `/portal/` - Debe mostrar login

5. **Dashboard:**
   - `/reportes/inteligencia/` - Debe mostrar widget de alertas

---

**¡Listo para ejecutar! 🚀**

