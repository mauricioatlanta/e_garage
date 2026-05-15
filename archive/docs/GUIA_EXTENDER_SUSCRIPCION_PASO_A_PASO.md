# 📋 Guía Paso a Paso: Extender Suscripción de un Suscriptor

**Fecha**: 2025-01-27

---

## 🎯 OBJETIVO

Extender la suscripción de un suscriptor específico desde el panel de administración.

---

## 🚀 PASO A PASO COMPLETO

### **PASO 1: Acceder al Panel de Suscriptores**

1. **Inicia el servidor** (si no está corriendo):
   ```bash
   cd E:\projecto\e_garage
   python manage.py runserver
   ```

2. **Inicia sesión como admin**:
   - Ve a: `http://localhost:8000/admin/`
   - Username: `mauricio`
   - Password: (tu contraseña)

3. **Accede al panel de suscriptores**:
   - Ve a: `http://localhost:8000/admin/suscriptores/`
   - O haz clic en el enlace si está disponible en el admin

---

### **PASO 2: Buscar el Suscriptor**

En el panel de suscriptores verás:

1. **Filtros disponibles**:
   - **Por País**: CL, US, MX, PE, CO, EC, BR, VE
   - **Por Status**: Activa, Vencida, Trial
   - **Por Días Restantes**: Crítico (≤1), Advertencia (≤5), Vencido
   - **Búsqueda**: Por nombre, email o teléfono

2. **Usar los filtros**:
   - Selecciona el país del suscriptor
   - O usa la búsqueda para encontrar por nombre/email/teléfono
   - Haz clic en "Filtrar" o presiona Enter

3. **Identificar el suscriptor**:
   - Busca en la tabla el nombre del taller
   - Verifica el email y teléfono
   - Revisa los días restantes y el status

---

### **PASO 3: Extender la Suscripción**

1. **Encontrar el botón de extensión**:
   - En la fila del suscriptor, busca el botón **"⏱️ Extender"**
   - Está en la columna "Acciones" (última columna)

2. **Hacer clic en "⏱️ Extender"**:
   - Se abrirá un modal (ventana emergente)
   - Verás el nombre de la empresa

3. **Seleccionar meses a extender**:
   - En el dropdown, selecciona:
     - **1 mes** (30 días)
     - **6 meses** (180 días)
     - **12 meses** (365 días)
   - ⚠️ Solo estas opciones están disponibles

4. **Confirmar extensión**:
   - Opcionalmente marca/desmarca "Enviar notificación" (por defecto está marcado)
   - Haz clic en el botón **"✅ Extender"**

---

### **PASO 4: Verificar la Extensión**

Después de hacer clic en "Extender":

1. **Mensaje de confirmación**:
   - Verás un mensaje verde de éxito
   - Ejemplo: "✅ Extensión de cortesía otorgada exitosamente por 6 mes(es)"

2. **Actualización automática**:
   - La tabla se actualizará automáticamente
   - Verás:
     - Nueva fecha de vencimiento
     - Nuevos días restantes
     - Status actualizado (si estaba vencido, ahora será "Activa")

3. **Notificaciones enviadas**:
   - El sistema enviará automáticamente:
     - **Email** al suscriptor con mensaje de agradecimiento
     - **WhatsApp** al teléfono registrado (si tiene teléfono)

---

## 📊 EJEMPLO VISUAL

### **Antes de Extender**:
```
Empresa: Taller Los Ángeles
Email: taller@ejemplo.com
Días Restantes: 3 días
Status: ⚠️ Advertencia
Vencimiento: 01/02/2025
```

### **Después de Extender (6 meses)**:
```
Empresa: Taller Los Ángeles
Email: taller@ejemplo.com
Días Restantes: 183 días
Status: ✅ Activa
Vencimiento: 01/08/2025
```

---

## 🔍 ALTERNATIVA: Extender desde Admin de Django

Si prefieres usar el admin estándar de Django:

### **PASO 1: Acceder a Empresas**

1. Ve a: `http://localhost:8000/admin/`
2. Busca la sección **"TALLER"** o **"Empresas"**
3. Haz clic en **"Empresas"**

### **PASO 2: Buscar la Empresa**

1. Usa la búsqueda o filtra por país
2. Haz clic en el nombre de la empresa

### **PASO 3: Extender Manualmente**

1. En la página de detalle, verás el campo **"Fecha fin"**
2. Puedes editarlo manualmente
3. **PERO**: Esto NO enviará notificaciones automáticas
4. **RECOMENDACIÓN**: Usa el panel de suscriptores para tener todas las funciones

---

## ⚠️ IMPORTANTE

### **Lo que SÍ hace el panel de suscriptores**:
- ✅ Extiende la fecha de vencimiento
- ✅ Actualiza el estado de la suscripción
- ✅ Sincroniza con el modelo `Suscripcion`
- ✅ Registra en auditoría (LogAuditoria)
- ✅ Envía email de notificación
- ✅ Envía WhatsApp de notificación
- ✅ Actualiza días restantes automáticamente

### **Lo que NO hace el admin estándar**:
- ❌ No envía notificaciones automáticas
- ❌ No registra en auditoría con razón
- ❌ No sincroniza automáticamente

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### **Problema 1: No veo el panel `/admin/suscriptores/`**

**Solución**:
1. Verifica que el servidor está corriendo
2. Verifica que estás autenticado como staff/admin
3. Verifica que las rutas están descomentadas en `gestion_taller/urls.py`
4. Reinicia el servidor:
   ```bash
   # Detener servidor (Ctrl+C)
   python manage.py runserver
   ```

---

### **Problema 2: Error 404 al acceder**

**Solución**:
1. Verifica que existe el archivo: `taller/views_extra/admin_suscriptores.py`
2. Verifica que existen los templates:
   - `templates/admin/suscriptores/lista_suscriptores.html`
   - `templates/admin/suscriptores/detalle_suscriptor.html`
3. Verifica que las rutas están descomentadas en `urls.py`

---

### **Problema 3: No se envían notificaciones**

**Solución**:
1. Verifica configuración de email en `settings.py`
2. Verifica configuración de WhatsApp
3. Revisa logs: `logs/django.log`
4. Verifica que el suscriptor tiene email y teléfono registrados

---

## 📋 CHECKLIST COMPLETO

- [ ] Servidor corriendo (`python manage.py runserver`)
- [ ] Iniciado sesión como admin (`/admin/`)
- [ ] Accedido al panel de suscriptores (`/admin/suscriptores/`)
- [ ] Encontrado el suscriptor (usando filtros/búsqueda)
- [ ] Clic en botón "⏱️ Extender"
- [ ] Seleccionado meses (1, 6 o 12)
- [ ] Clic en "✅ Extender"
- [ ] Verificado mensaje de éxito
- [ ] Verificado actualización de fecha y días
- [ ] Verificado que llegaron notificaciones (email + WhatsApp)

---

## 🎯 RESUMEN RÁPIDO

1. **URL**: `http://localhost:8000/admin/suscriptores/`
2. **Buscar**: Usa filtros o búsqueda
3. **Extender**: Clic en "⏱️ Extender" → Seleccionar meses → "✅ Extender"
4. **Verificar**: Mensaje de éxito y actualización automática

---

**Última actualización**: 2025-01-27

