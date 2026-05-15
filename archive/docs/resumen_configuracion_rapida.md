# Resumen Rápido: Configuración WhatsApp

## Valores que necesitas obtener de Meta:

1. **Phone Number ID**: En WhatsApp > API Setup
2. **Access Token**: En WhatsApp > API Setup > Access Tokens
3. **Verify Token**: `egarage_secret_verify_2026` (lo defines tú)

## Pasos rápidos:

1. ✅ Crear app en Meta → "Crear app" → "Negocio"
2. ✅ Agregar producto WhatsApp → "Configurar"
3. ✅ Anotar Phone Number ID
4. ✅ Generar Access Token
5. ✅ Configurar Webhook:
   - Callback URL: `https://tu-ngrok-url.ngrok.io/whatsapp/webhook/`
   - Verify Token: `egarage_secret_verify_2026`
6. ✅ Actualizar `.env` con los valores
7. ✅ Suscribirse a eventos: `messages`, `message_deliveries`

## Comandos útiles:

```bash
# Iniciar servidor Django
python manage.py runserver

# Iniciar ngrok (en otra terminal)
ngrok http 8000

# Probar webhook
python probar_webhook_directo.py
```
