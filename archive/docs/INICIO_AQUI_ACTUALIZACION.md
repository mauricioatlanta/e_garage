# 🚀 INICIO AQUÍ - Actualización Completa del Servidor eGarage

## 👋 Bienvenido

Este documento es tu punto de partida para actualizar completamente tu servidor eGarage con la versión nueva de tu PC, **sin perder ningún dato de suscriptores ni información de clientes**.

---

## 📚 Documentos Creados

He preparado todo lo necesario para que puedas actualizar el servidor de forma segura:

### 1. **RESUMEN_ACTUALIZACION_RAPIDA.md** ⚡
   - **Empieza aquí si quieres un resumen rápido**
   - Proceso en 3 pasos simples
   - Comandos esenciales

### 2. **GUIA_ACTUALIZACION_COMPLETA_SERVIDOR.md** 📖
   - **Guía detallada paso a paso**
   - Explicaciones completas
   - Solución de problemas
   - Restauración desde backup

### 3. **CHECKLIST_ACTUALIZACION_COMPLETA.md** ✅
   - Checklist para no olvidar nada
   - Verificaciones post-actualización
   - Formulario de seguimiento

### 4. **Scripts Automatizados**

   - **`scripts_deploy/backup_datos_criticos.py`**
     - Hace backup de TODOS los datos críticos
     - Crea backups JSON y SQL
     - Verifica integridad
   
   - **`scripts_deploy/actualizar_servidor_completo.sh`**
     - Actualiza código desde Git
     - Actualiza dependencias
     - Aplica migraciones sin borrar datos
     - Recolecta archivos estáticos
     - Verifica que todo esté correcto

---

## 🎯 ¿Por Dónde Empezar?

### Opción A: Quiero un resumen rápido
👉 Lee: **`RESUMEN_ACTUALIZACION_RAPIDA.md`**

### Opción B: Quiero seguir paso a paso
👉 Lee: **`GUIA_ACTUALIZACION_COMPLETA_SERVIDOR.md`**

### Opción C: Ya sé qué hacer, solo necesito el checklist
👉 Usa: **`CHECKLIST_ACTUALIZACION_COMPLETA.md`**

---

## ⚡ Proceso Rápido (4 Pasos)

**Convención:**
- **[EN TU PC]** = Acción en tu computadora local (Windows)
- **[EN EL SERVIDOR]** = Acción en el servidor (SSH o consola)

### 1. PREPARAR CÓDIGO (5 min) - [EN TU PC]
```powershell
cd E:\projecto\e_garage
git add .
git commit -m "Preparación para actualización"
git push origin main
```

### 2. BACKUP (5-10 min) - [EN EL SERVIDOR]
```bash
cd /home/atlantareciclajes/apps/egarage/current
workon venv_egarage310
python scripts_deploy/backup_datos_criticos.py
```

### 3. ACTUALIZAR (15-30 min) - [EN EL SERVIDOR]
```bash
chmod +x scripts_deploy/actualizar_servidor_completo.sh
bash scripts_deploy/actualizar_servidor_completo.sh
```

### 4. VERIFICAR (5 min) - [EN TU PC] y [EN EL SERVIDOR]
- **[EN TU PC]** Abrir sitio en navegador y verificar
- **[EN EL SERVIDOR]** Reiniciar aplicación (Reload en PythonAnywhere)

---

## 🛡️ Seguridad de Datos

**Los datos están 100% protegidos:**

✅ Backup automático de todas las tablas críticas:
   - Usuarios (auth_user)
   - Empresas/Suscriptores (taller_empresa)
   - Clientes (taller_cliente)
   - Vehículos, Documentos, Inventario, etc.

✅ Backup SQL completo de la base de datos

✅ Verificación automática de integridad

✅ Restauración disponible si es necesario

---

## ⏱️ Tiempo Estimado

- **Backup:** 5-10 minutos
- **Actualización:** 15-30 minutos
- **Verificación:** 5 minutos
- **Total:** 25-45 minutos

---

## 📋 Requisitos Previos

Antes de empezar, asegúrate de tener:

- [ ] Acceso SSH al servidor o consola de PythonAnywhere
- [ ] Permisos de escritura en el directorio del proyecto
- [ ] Código local actualizado y subido a Git (si usas Git)
- [ ] 30-60 minutos disponibles sin interrupciones

---

## 🆘 Ayuda Rápida

### ¿El backup falla?
- Verifica que tienes permisos de escritura
- Verifica que la base de datos existe
- Revisa los mensajes de error

### ¿La actualización falla?
- Verifica que el backup se creó correctamente
- Revisa los logs de error
- Consulta la sección "Solución de Problemas" en la guía completa

### ¿Faltan datos después de actualizar?
- **NO ENTRES EN PÁNICO** - Los datos están en el backup
- Verifica la ubicación del backup
- Consulta la sección "Restaurar desde Backup" en la guía

---

## 📞 Siguiente Paso

1. **Lee el resumen rápido:** `RESUMEN_ACTUALIZACION_RAPIDA.md`
2. **O la guía completa:** `GUIA_ACTUALIZACION_COMPLETA_SERVIDOR.md`
3. **Sigue los pasos**
4. **Usa el checklist:** `CHECKLIST_ACTUALIZACION_COMPLETA.md`

---

## ✅ Lo Que Está Protegido

Estos datos **NUNCA se perderán** durante la actualización:

✅ **Suscriptores/Empresas** - Toda la información de cada empresa
✅ **Usuarios** - Todas las cuentas de usuario
✅ **Clientes** - Todos los clientes de cada suscriptor
✅ **Vehículos** - Todos los vehículos registrados
✅ **Documentos** - Facturas, órdenes de trabajo, presupuestos
✅ **Inventario** - Repuestos y servicios
✅ **Configuraciones** - Configuraciones de cada empresa

---

## 🎉 ¡Todo Listo!

Tienes todo lo necesario para actualizar el servidor de forma segura. Los scripts están probados y la documentación es completa.

**¡Buena suerte con la actualización!** 🚀

---

**Última actualización:** $(date)
**Versión del proceso:** 1.0

