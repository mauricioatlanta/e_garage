# 🚀 Instrucciones para Actualizar TODOS los Cambios

## ✅ Problemas Solucionados:

1. ✅ Cuadros de debug eliminados (morado, amarillo, verde, azul)
2. ✅ Botones de navegación con texto tecnológico (Orbitron, cyan, glow)
3. ✅ Botones de acción (ver/editar/borrar) más grandes en móviles
4. ✅ Script de estado→ciudad optimizado para móviles
5. ✅ Espías de debug para scroll y focus activados

---

## 📁 Archivos Modificados:

### **Templates Base:**
1. `templates/base.html`
   - Espías de scroll y focus
   - Botones con texto tecnológico inline
   - starfield.js desactivado temporalmente

2. `templates/taller/common/base.html`
   - Espías de scroll y focus

### **Templates de Clientes USA:**
3. `templates/us/en/clientes/crear_cliente.html` - Mejorado + debug eliminado
4. `templates/us/en/clientes/editar_cliente.html` - Debug eliminado
5. `templates/us/es/clientes/crear_cliente.html` - Debug eliminado
6. `templates/us/es/clientes/editar_cliente.html` - Debug eliminado
7. `templates/us/es/clientes/cliente_form.html` - Debug eliminado
8. `templates/taller/us/en/clientes/crear_cliente.html` - Debug eliminado
9. `templates/taller/us/en/clientes/cliente_form.html` - Debug eliminado
10. `templates/taller/us/es/clientes/cliente_form.html` - Debug eliminado

### **Templates de Clientes Comunes:**
11. `templates/taller/common/clientes/cliente_form.html` - Debug morado eliminado
12. `templates/taller/common/clientes/cliente_list.html` - Botones más grandes

---

## 🔄 PASO 1: Actualizar en Servidor Local

```powershell
# Si el servidor está corriendo, presiona Ctrl+C
# No es necesario ejecutar nada más, los templates se recargan automáticamente
# Solo reinicia si hay problemas:
python manage.py runserver 0.0.0.0:8000
```

### Verificar en Local:
- PC: `http://127.0.0.1:8000/us/clientes/crear/`
- Celular: `http://192.168.1.106:8000/us/clientes/crear/`

---

## 📤 PASO 2: Subir a Producción (PythonAnywhere)

### Opción A: Script Automático

```powershell
cd E:\projecto\e_garage

# Subir todos los archivos
.\actualizar_todos_produccion.ps1
```

### Opción B: Manual (Recomendado)

```powershell
cd E:\projecto\e_garage

# 1. Base templates
scp .\templates\base.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/

scp .\templates\taller\common\base.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/taller/common/

# 2. Templates USA - clientes
scp .\templates\us\en\clientes\crear_cliente.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/us/en/clientes/

scp .\templates\us\en\clientes\editar_cliente.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/us/en/clientes/

scp .\templates\us\es\clientes\crear_cliente.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/us/es/clientes/

scp .\templates\us\es\clientes\editar_cliente.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/us/es/clientes/

scp .\templates\us\es\clientes\cliente_form.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/us/es/clientes/

# 3. Templates taller USA
scp .\templates\taller\us\en\clientes\crear_cliente.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/taller/us/en/clientes/

scp .\templates\taller\us\en\clientes\cliente_form.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/taller/us/en/clientes/

scp .\templates\taller\us\es\clientes\cliente_form.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/taller/us/es/clientes/

# 4. Templates comunes
scp .\templates\taller\common\clientes\cliente_form.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/taller/common/clientes/

scp .\templates\taller\common\clientes\cliente_list.html atlantareciclajes@ssh.pythonanywhere.com:~/apps/egarage/current/templates/taller/common/clientes/
```

### Reiniciar Aplicación:

```powershell
ssh atlantareciclajes@ssh.pythonanywhere.com
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
exit
```

---

## 🧹 PASO 3: Limpiar Caché

### En tu Celular:
**Chrome Android:**
- Configuración → Privacidad → Borrar datos de navegación
- Marcar "Imágenes y archivos en caché"
- Presionar "Borrar datos"

**O abrir en modo INCÓGNITO**

---

## ✅ Verificación Final

Después de actualizar, verifica:

1. ✅ **No hay cuadros de colores** en la cabecera
2. ✅ **Botones muestran texto** (AJUSTES, CENTRO, CLIENTES, etc.)
3. ✅ **Texto con fuente Orbitron** y color cyan brillante
4. ✅ **Botones ver/editar/borrar** son más grandes en móviles
5. ✅ **Ciudades cargan** al seleccionar estado
6. ✅ **Sin scroll automático** (con starfield desactivado)

---

## 🔍 Para Debug de Scroll (si persiste):

Si el scroll automático sigue ocurriendo:

1. Abre Chrome DevTools en modo móvil
2. Ve a Console
3. Verás logs de los espías:
   ```
   🎯 *** focus() en: <input ...>
   🔍 *** window.scrollTo llamado con: 0 0
   ```
4. Copia el stack trace completo y compártelo

---

## 📊 Resumen:

- **12 archivos modificados** ✅
- **7 cuadros de debug eliminados** ✅
- **Botones mejorados para móviles** ✅
- **Espías de debug activos** ✅


