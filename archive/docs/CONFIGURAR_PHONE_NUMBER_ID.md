# 📱 Cómo Obtener y Configurar Phone Number ID

## 🎯 ¿Qué es Phone Number ID?

El `phone_number_id` es el identificador único que Meta asigna a tu número de teléfono de WhatsApp Business. Es necesario para que el sistema sepa a qué empresa pertenece cada mensaje.

## 🔧 Opción 1: Para Pruebas Locales (Sin Meta)

Si solo estás probando localmente y aún no tienes Meta configurado, puedes usar un valor de prueba:

```python
PHONE_NUMBER_ID = "test_123"  # Valor de prueba
```

**Importante:** Luego deberás crear la configuración en Admin con este mismo valor.

## 🔧 Opción 2: Con Meta Cloud API Configurado

Si ya tienes Meta Cloud API configurado:

1. **Obtén el Phone Number ID desde Meta:**
   - Ve a [Meta for Developers](https://developers.facebook.com/)
   - Selecciona tu App
   - Ve a "WhatsApp" → "API Setup"
   - Copia el "Phone number ID"

2. **Configúralo en el simulador:**
   - Edita `test_bot.py` línea 18
   - O usa la opción 6 del menú del simulador

3. **Configúralo en Admin:**
   - Ve a `http://127.0.0.1:8000/admin/whatsapp/empresawhatsappconfig/add/`
   - Selecciona una empresa
   - Pega el `phone_number_id` en el campo correspondiente
   - Configura también `allowed_operator_phone` (tu teléfono de prueba)

## 📋 Pasos Detallados para Configurar en Admin

### Paso 1: Crear Configuración en Admin

1. Inicia el servidor:
   ```bash
   python manage.py runserver
   ```

2. Ve a Admin:
   ```
   http://127.0.0.1:8000/admin/
   ```

3. Navega a:
   ```
   WhatsApp → Configuraciones WhatsApp Empresas → Agregar
   ```

4. Completa el formulario:
   - **Empresa**: Selecciona una empresa existente
   - **Phone number id**: Pega el ID de Meta (o usa "test_123" para pruebas)
   - **Allowed operator phone**: Tu teléfono de prueba (ej: `56912345678`)
   - **Is enabled**: ✅ Marcado
   - **Enable audio**: ✅ Marcado (si quieres probar NLP)
   - **Enable ocr**: ✅ Marcado (si quieres probar OCR)

5. Guarda

### Paso 2: Configurar en el Simulador

**Opción A: Editar archivo**
```python
# En test_bot.py, línea 18
PHONE_NUMBER_ID = "el_valor_que_pegaste_en_admin"
```

**Opción B: Usar el menú**
```bash
python test_bot.py
# Selecciona opción 6
# Pega el phone_number_id
```

## ✅ Verificación

Para verificar que todo está correcto:

1. **Verifica en Admin:**
   - El `phone_number_id` en Admin debe coincidir con el del simulador
   - El `allowed_operator_phone` debe coincidir con `PHONE_TEST` en el simulador

2. **Prueba el simulador:**
   ```bash
   python test_bot.py
   # Selecciona opción 1
   # Escribe "Nuevo"
   ```

3. **Revisa los logs:**
   - Deberías ver: `INFO whatsapp.views Configuración encontrada para phone_number_id: ...`
   - NO deberías ver: `WARNING whatsapp.views Configuración no encontrada...`

## 🐛 Troubleshooting

### Error: "Configuración no encontrada"

**Causa:** El `phone_number_id` no coincide entre Admin y el simulador.

**Solución:**
1. Verifica el valor en Admin: `/admin/whatsapp/empresawhatsappconfig/`
2. Verifica el valor en `test_bot.py` línea 18
3. Asegúrate de que sean exactamente iguales (sin espacios, sin mayúsculas/minúsculas diferentes)

### Error: "Teléfono no autorizado"

**Causa:** El `PHONE_TEST` no coincide con `allowed_operator_phone` en Admin.

**Solución:**
1. Verifica `PHONE_TEST` en `test_bot.py` línea 16
2. Verifica `allowed_operator_phone` en Admin
3. Asegúrate de que sean exactamente iguales (formato: `56912345678`)

### No Puedo Acceder a Admin

**Solución:**
1. Crea un superusuario:
   ```bash
   python manage.py createsuperuser
   ```
2. Inicia sesión en `/admin/`
3. Crea la configuración de WhatsApp

## 💡 Valores de Prueba Rápida

Si solo quieres probar rápidamente sin configurar Meta:

```python
# En test_bot.py
PHONE_NUMBER_ID = "test_123"
PHONE_TEST = "56912345678"
```

Luego en Admin, crea una configuración con:
- **Phone number id**: `test_123`
- **Allowed operator phone**: `56912345678`
- **Empresa**: Cualquier empresa existente

---

**¡Con esto deberías poder probar el sistema completamente!** 🚀
