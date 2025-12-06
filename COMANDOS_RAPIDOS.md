# ⚡ Comandos Rápidos - Rediseño Clientes

## 🚀 Despliegue Automático (Más Fácil)

```powershell
# Prueba local + despliegue servidor (TODO EN UNO)
.\deploy_clientes_redesign.ps1 -Both
```

---

## 📋 Comandos Esenciales

### 1️⃣ Backup Rápido
```powershell
Copy-Item ".\templates\taller\common\clientes\lista_clientes.html" ".\backup_$(Get-Date -Format 'yyyyMMdd').html"
```

### 2️⃣ Probar Localmente
```powershell
python manage.py runserver
# Abre: http://localhost:8000/us/clientes/
```

### 3️⃣ Subir a Git
```powershell
git add templates/taller/common/clientes/lista_clientes.html
git commit -m "🎨 Rediseño futurista clientes"
git push origin main
```

### 4️⃣ Comandos en Servidor
```bash
ssh usuario@tuservidor.com
cd /ruta/al/proyecto
git pull origin main
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

### 5️⃣ Rollback (Emergencia)
```powershell
Copy-Item ".\backup_FECHA.html" ".\templates\taller\common\clientes\lista_clientes.html" -Force
```

---

## 🔍 Verificación

### Verificar Clases CSS
```powershell
Select-String -Path ".\templates\taller\common\clientes\lista_clientes.html" -Pattern "btn-futuristic"
```

### Ver Cambios
```powershell
git diff templates/taller/common/clientes/lista_clientes.html
```

### Limpiar Caché
```
Navegador: Ctrl + Shift + Del > Clear Cache
O: Ctrl + F5 (forzar recarga)
```

---

## 📱 URLs de Prueba

```
Local:
  http://localhost:8000/us/clientes/
  http://localhost:8000/cl/clientes/

Producción:
  https://www.egarage.cl/us/clientes/
  https://www.egarage.cl/cl/clientes/
```

---

## 🎯 Checklist Visual

```
✅ Bordes cyan con glow
✅ Botones grandes en móvil
✅ Texto visible en botones
✅ Iconos grandes
✅ Animaciones suaves
✅ Colores cyber (cyan, purple, gold)
```

---

## 🔧 Solución de Problemas

### No se ven los estilos
```powershell
# Ctrl + F5 en el navegador
# O:
python manage.py collectstatic --noinput
```

### Cambios no aparecen en servidor
```bash
# En el servidor:
git pull origin main
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
```

### Error de permisos en servidor
```bash
sudo chown -R www-data:www-data /ruta/al/proyecto
sudo chmod -R 755 /ruta/al/proyecto
```

---

## 📞 Archivos Importantes

```
templates/taller/common/clientes/lista_clientes.html  ← Archivo modificado
RESUMEN_REDISENO_CLIENTES.md                         ← Resumen ejecutivo
INSTRUCCIONES_REDISENO_CLIENTES.md                   ← Guía completa
deploy_clientes_redesign.ps1                         ← Script automático
COMANDOS_RAPIDOS.md                                  ← Este archivo
```

---

## ⚡ Un Solo Comando (Lo Más Fácil)

Para hacer TODO automáticamente:

```powershell
.\deploy_clientes_redesign.ps1 -Both
```

Este comando:
1. ✅ Hace backup
2. ✅ Verifica cambios
3. ✅ Prueba local
4. ✅ Commit + Push a Git
5. ✅ Te da instrucciones para servidor

---

**¡Listo en 1 minuto! 🚀**




