# Guía Completa: Configurar WhatsApp Business API en Meta

## Paso 1: Crear una App en Meta

1. **En la página actual** (https://developers.facebook.com/apps/), haz clic en el botón verde **"Crear app"** (Create app)

2. **Selecciona el tipo de app:**
   - Elige **"Negocio"** (Business) o **"Otro"** (Other)
   - Haz clic en **"Siguiente"**

3. **Completa la información básica:**
   - **Nombre de la app**: `eGarage Air` (o el nombre que prefieras)
   - **Email de contacto**: Tu email
   - **Propósito de la app**: Selecciona "WhatsApp"
   - Haz clic en **"Crear app"**

## Paso 2: Agregar WhatsApp al Producto

1. **En el dashboard de tu app**, busca la sección **"Agregar productos a tu app"**
   - Busca **"WhatsApp"** en la lista
   - Haz clic en **"Configurar"** o **"Set up"**

2. **Si te pide seleccionar un tipo de cuenta:**
   - Selecciona **"WhatsApp Business API"** o **"Cloud API"**

## Paso 3: Configurar el Número de Teléfono

1. **Ve a WhatsApp > API Setup** (o **Configuración de API**)
2. **Temporal Number (Número Temporal):**
   - Meta te proporcionará un número temporal para pruebas
   - Anota este número: `+1 XXX XXX XXXX` (aparecerá en la pantalla)

3. **Phone Number ID:**
   - Anota el **Phone Number ID** que aparece (ej: `123456789012345`)
   - Este es el que necesitas para `META_WA_PHONE_NUMBER_ID` en tu `.env`

## Paso 4: Obtener el Access Token

1. **En WhatsApp > API Setup**, busca la sección **"Access Tokens"**
2. **Token temporal (para desarrollo):**
   - Haz clic en **"Generate token"** o **"Generar token"**
   - Copia el token generado (es largo, algo como: `EAAxxxxxxxxxxxxx...`)
   - Este es el que necesitas para `META_WA_TOKEN` en tu `.env`

   ⚠️ **IMPORTANTE**: Este token expira en 24 horas. Para producción, necesitarás un token permanente.

## Paso 5: Configurar el Webhook

1. **Ve a WhatsApp > Configuration** (o **Configuración**)

2. **En la sección "Webhook":**
   - Haz clic en **"Edit"** o **"Editar"**

3. **Ingresa la información:**
   - **Callback URL**: 
     - Para pruebas locales: Usa ngrok (ver Paso 6)
     - Para producción: `https://tu-dominio.com/whatsapp/webhook/`
   - **Verify Token**: `egarage_secret_verify_2026`
     - Este debe coincidir exactamente con el que está en tu `.env`

4. **Haz clic en "Verify and Save"** (Verificar y guardar)
   - Meta enviará una petición GET a tu webhook
   - Si todo está correcto, verás un check verde ✅

## Paso 6: Configurar ngrok para Pruebas Locales

Meta requiere HTTPS, así que para pruebas locales necesitas ngrok:

1. **Instala ngrok:**
   ```bash
   # Descarga desde https://ngrok.com/download
   # O con chocolatey (Windows):
   choco install ngrok
   ```

2. **Inicia ngrok:**
   ```bash
   ngrok http 8000
   ```

3. **Copia la URL HTTPS** que ngrok te da:
   - Ejemplo: `https://abc123.ngrok.io`
   - Usa esta URL en Meta: `https://abc123.ngrok.io/whatsapp/webhook/`

4. **⚠️ IMPORTANTE**: 
   - Cada vez que reinicies ngrok, obtendrás una URL diferente
   - Deberás actualizar la Callback URL en Meta cada vez

## Paso 7: Actualizar tu archivo .env

Una vez que tengas todos los valores, actualiza tu `.env`:

```env
# WhatsApp / Meta Cloud API
META_WA_TOKEN=tu_token_generado_aqui
META_WA_PHONE_NUMBER_ID=tu_phone_number_id_aqui
META_WA_VERIFY_TOKEN=egarage_secret_verify_2026
```

## Paso 8: Suscribirte a Eventos del Webhook

1. **En WhatsApp > Configuration > Webhook**
2. **Haz clic en "Manage"** o **"Gestionar"**
3. **Marca los eventos que quieres recibir:**
   - ✅ `messages` - Recibir mensajes
   - ✅ `message_deliveries` - Confirmaciones de entrega
   - ✅ `message_reads` - Confirmaciones de lectura (opcional)
   - ✅ `messaging_handovers` - Transferencias (opcional)

4. **Haz clic en "Save"**

## Paso 9: Probar el Webhook

1. **Asegúrate de que tu servidor Django esté corriendo:**
   ```bash
   python manage.py runserver
   ```

2. **Asegúrate de que ngrok esté corriendo** (si estás en local)

3. **Envía un mensaje de prueba:**
   - Desde tu teléfono, envía un mensaje al número temporal de Meta
   - Deberías ver el mensaje en los logs de Django

## Troubleshooting

### El webhook no se verifica
- Verifica que el servidor Django esté corriendo
- Verifica que ngrok esté corriendo (si es local)
- Verifica que el `META_WA_VERIFY_TOKEN` en `.env` coincida exactamente con el de Meta
- Revisa los logs del servidor Django

### No recibo mensajes
- Verifica que estés suscrito a los eventos correctos
- Verifica que el número desde el que envías esté en `allowed_operator_phone` en el admin
- Revisa los logs del servidor Django

### El token expira
- Los tokens temporales expiran en 24 horas
- Para producción, configura un System User Token permanente
- Ve a: Business Settings > System Users > Create System User

## Próximos Pasos

Una vez que el webhook esté funcionando:

1. **Configura una empresa en el admin de Django:**
   - Ve a `/admin/whatsapp/empresawhatsappconfig/add/`
   - Completa los datos con los valores de Meta

2. **Prueba el flujo completo:**
   - Envía "Nuevo" o "🆕" al número de WhatsApp
   - El bot debería responder según el flujo configurado

## Recursos Útiles

- **Documentación oficial**: https://developers.facebook.com/docs/whatsapp
- **API Reference**: https://developers.facebook.com/docs/whatsapp/cloud-api
- **Webhook Guide**: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks
