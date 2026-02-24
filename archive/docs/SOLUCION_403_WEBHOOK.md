# Solución: Error 403 "Verification failed" en Webhook WhatsApp

## Problema
El webhook devuelve `403 Forbidden` con el mensaje "Verification failed" cuando Meta Cloud API intenta verificar el webhook.

## Causa
El token de verificación (`META_WA_VERIFY_TOKEN`) no está siendo leído por Django, o el servidor no se ha reiniciado después de configurar el `.env`.

## Solución

### 1. Verificar que el archivo `.env` existe y tiene el token

El archivo `.env` debe estar en la raíz del proyecto (`E:\projecto\e_garage\.env`) y contener:

```env
META_WA_VERIFY_TOKEN=egarage_secret_verify_2026
```

### 2. Reiniciar el servidor Django

**IMPORTANTE**: Después de crear o modificar el archivo `.env`, debes **reiniciar el servidor Django** para que cargue las nuevas variables de entorno.

1. Detén el servidor (Ctrl+C en la terminal donde está corriendo)
2. Inicia el servidor nuevamente:
   ```bash
   python manage.py runserver
   ```

### 3. Probar la verificación

Ejecuta el script de prueba:
```bash
python test_webhook_verification.py
```

Deberías ver:
```
[OK] VERIFICACION EXITOSA
Challenge devuelto: 1234567890
```

### 4. Configurar en Meta Cloud API

Una vez que el webhook funcione localmente:

1. Ve a https://developers.facebook.com/apps/
2. Selecciona tu app
3. Ve a **WhatsApp > Configuration**
4. En la sección **Webhook**, haz clic en **Edit**
5. Ingresa:
   - **Callback URL**: `https://tu-dominio.com/whatsapp/webhook/` (o usa ngrok para pruebas locales)
   - **Verify Token**: `egarage_secret_verify_2026` (el mismo que está en tu `.env`)
6. Haz clic en **Verify and Save**

**Nota**: Meta requiere HTTPS. Para pruebas locales, usa [ngrok](https://ngrok.com/):
```bash
ngrok http 8000
```
Luego usa la URL de ngrok (ej: `https://abc123.ngrok.io/whatsapp/webhook/`) en Meta.

## Verificación Manual

Puedes probar manualmente el webhook desde el navegador o con curl:

```bash
curl "http://127.0.0.1:8000/whatsapp/webhook/?hub.mode=subscribe&hub.verify_token=egarage_secret_verify_2026&hub.challenge=1234567890"
```

Debería devolver: `1234567890`

## Troubleshooting

### El token sigue sin funcionar

1. Verifica que el archivo `.env` está en la raíz del proyecto
2. Verifica que no hay espacios extra en el `.env`:
   ```env
   # Correcto
   META_WA_VERIFY_TOKEN=egarage_secret_verify_2026
   
   # Incorrecto (tiene espacios)
   META_WA_VERIFY_TOKEN = egarage_secret_verify_2026
   ```
3. Ejecuta `python verificar_webhook.py` para ver el diagnóstico completo
4. Revisa los logs del servidor Django para ver qué token está recibiendo

### Ver logs del servidor

El webhook ahora tiene logging mejorado. Revisa la consola donde corre `runserver` para ver:
```
Verificación webhook: mode=subscribe, token_recibido=..., token_configurado=..., challenge=...
```
