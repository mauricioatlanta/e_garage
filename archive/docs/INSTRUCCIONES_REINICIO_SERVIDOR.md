# ⚠️ IMPORTANTE: Reiniciar el Servidor Django

## Problema Actual
El webhook devuelve `403 Verification failed: Token no configurado` porque el servidor Django no ha cargado las variables de entorno del archivo `.env`.

## Solución: Reiniciar el Servidor

### Pasos:

1. **Detén el servidor Django actual:**
   - Ve a la terminal donde está corriendo `python manage.py runserver`
   - Presiona `Ctrl+C` para detenerlo

2. **Reinicia el servidor:**
   ```bash
   python manage.py runserver
   ```

3. **Prueba el webhook nuevamente:**
   ```bash
   python probar_webhook_directo.py
   ```

## ¿Por qué es necesario reiniciar?

Django carga las variables de entorno del archivo `.env` **solo cuando se inicia el servidor**. Si creaste o modificaste el archivo `.env` después de que el servidor ya estaba corriendo, Django no verá los cambios hasta que lo reinicies.

## Verificación

Después de reiniciar, deberías ver:
```
[OK] VERIFICACION EXITOSA!
Challenge devuelto: 1234567890
```

## Cambios Realizados

He mejorado el código para que:
1. ✅ Intente leer el token desde `settings` primero
2. ✅ Si no está en `settings`, intente leerlo directamente del `.env` como fallback
3. ✅ Proporcione mensajes de error más claros
4. ✅ Mejore el logging para debugging

Pero **aún necesitas reiniciar el servidor** para que Django cargue el `.env` correctamente.

## Próximos Pasos

Una vez que el webhook funcione localmente:

1. **Para pruebas locales con Meta:**
   - Usa [ngrok](https://ngrok.com/) para crear un túnel HTTPS:
     ```bash
     ngrok http 8000
     ```
   - Usa la URL de ngrok (ej: `https://abc123.ngrok.io/whatsapp/webhook/`) en Meta

2. **Configurar en Meta Cloud API:**
   - Ve a https://developers.facebook.com/apps/
   - Selecciona tu app > WhatsApp > Configuration
   - En "Webhook", ingresa:
     - **Callback URL**: `https://tu-dominio.com/whatsapp/webhook/` (o la URL de ngrok)
     - **Verify Token**: `egarage_secret_verify_2026`
   - Haz clic en "Verify and Save"
