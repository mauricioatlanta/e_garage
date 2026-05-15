# 🚀 eGarage Air - WhatsApp v2 Final - Guía de Configuración

## 📋 Resumen

eGarage Air es un módulo conversacional por WhatsApp que permite a los dueños de talleres gestionar el ingreso y proceso de vehículos sin tocar el teclado, mediante fotos (OCR), audios (IA) y mensajes de texto.

## 🔧 Instalación

### 1. Migraciones

```bash
python manage.py migrate whatsapp
```

### 2. Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```bash
# --- CONFIGURACIÓN META WHATSAPP API ---
# El Token de acceso permanente (System User Access Token) de Meta
META_WA_TOKEN=tu_token_de_acceso_largo_aqui

# El identificador numérico de tu número de teléfono en Meta
META_WA_PHONE_NUMBER_ID=tu_phone_number_id_aqui

# La palabra secreta que tú elijas para que Meta verifique tu Webhook
META_WA_VERIFY_TOKEN=egarage_secret_verify_2026

# --- CONFIGURACIÓN DE INTELIGENCIA ARTIFICIAL (Opcional) ---
# Para transcripción de audio y extracción de datos
OPENAI_API_KEY=tu_api_key_de_openai
# O si prefieres Google para el análisis de texto
GEMINI_API_KEY=tu_api_key_de_google

# --- CONFIGURACIÓN OCR (Opcional) ---
# Para reconocimiento de patentes desde imágenes
GOOGLE_VISION_API_KEY=tu_api_key_aqui
```

### 3. Configurar Empresa en Admin

1. Ve a `/admin/whatsapp/empresawhatsappconfig/add/`
2. Selecciona una empresa
3. Ingresa el `phone_number_id` de Meta
4. Ingresa el teléfono del operador autorizado (formato: `56912345678`)
5. Activa las funcionalidades que desees (audio, OCR)

## 🌐 Configuración del Webhook en Meta

### URL del Webhook

```
https://tu-dominio.com/whatsapp/webhook/
```

### Verificación

Meta enviará un GET request con estos parámetros:
- `hub.mode=subscribe`
- `hub.verify_token=egarage_secret_verify_2026` (el que configuraste)
- `hub.challenge=<número aleatorio>`

El sistema responderá automáticamente con el `challenge` si el token coincide.

### Permisos Requeridos

En el Panel de Desarrolladores de Meta, asegúrate de activar:
- ✅ `messages` - Para recibir mensajes
- ✅ `message_deliveries` - Para recibir estados de entrega

### HTTPS Obligatorio

⚠️ **IMPORTANTE**: Meta solo acepta URLs con HTTPS. Para pruebas locales:
- Usa [ngrok](https://ngrok.com/) para crear un túnel HTTPS
- Ejemplo: `ngrok http 8000` y usa la URL proporcionada

## 📱 Uso

### Flujo de Conversación

1. **Inicio**: El operador envía "Nuevo" o "🆕"
2. **Patente**: Envía una foto de la patente (OCR automático)
3. **Kilometraje**: Ingresa el kilometraje actual
4. **Acciones**: Menú de botones:
   - 🛠 Servicio
   - 🔩 Repuesto
   - 🏢 Externo
   - 📸 Evidencia
   - ✅ Finalizar

### Operador Único

Solo el teléfono configurado en `allowed_operator_phone` puede usar el sistema. Otros números recibirán un mensaje de error.

## 🏗️ Arquitectura

### Estructura de Archivos

```
whatsapp/
├── models.py          # EmpresaWhatsAppConfig, WhatsAppSession
├── views.py           # Webhook (GET verificación, POST recepción)
├── urls.py            # Rutas de la app
├── admin.py           # Configuración de admin
└── services/
    ├── meta.py        # Cliente Meta Cloud API
    ├── flow.py        # Máquina de Estados
    ├── nlp.py         # Procesamiento de IA
    └── ocr.py         # Reconocimiento de patentes
```

### Estados de la Sesión

- `IDLE`: Inactivo
- `WAITING_PLATE`: Esperando foto de patente
- `WAITING_MILEAGE`: Esperando kilometraje
- `WAITING_ACTION`: Esperando acción del menú
- `WAITING_CONFIRM`: Esperando confirmación

### TTL de Sesión

Las sesiones expiran después de 30 minutos de inactividad.

## 🔐 Seguridad

- ✅ Validación de operador único
- ✅ Verificación de token en webhook
- ✅ TTL de sesiones
- ✅ Logging de todas las interacciones

## 🤖 Procesamiento de NLP (Inteligencia Artificial)

El sistema incluye procesamiento de NLP completo que entiende jerga de talleres:

### Características

- ✅ **Transcripción de Audio**: Usa OpenAI Whisper para convertir audio a texto
- ✅ **Procesamiento de Texto**: Usa GPT-4o-mini o Gemini Pro para extraer información estructurada
- ✅ **Entiende Jerga**: Reconoce términos como "lucas", "balatas", "pega", etc.
- ✅ **Conversión de Precios**: "50 lucas" → 50000, "100 bucks" → 100
- ✅ **Modo Manual**: Si confidence < 0.70, muestra botones para entrada manual

### Acciones Soportadas

- `CREATE_OT`: Crear nueva Orden de Trabajo
- `ADD_SERVICE`: Agregar servicio interno
- `ADD_PART`: Agregar repuesto
- `ADD_OUTSOURCED`: Agregar servicio externo
- `GET_SUMMARY`: Obtener resumen del día

### Ejemplos de Uso

**Texto:**
```
Usuario: "Abre una orden para el Toyota patente ABCD12 de Don Juan, por un cambio de aceite"
→ Crea OT con patente, cliente y servicio
```

**Audio:**
```
Usuario: [Audio] "Cámbiame las balatas al Corsa, cobrale 40 lucas"
→ Agrega servicio "Cambio de balatas" con precio 40000
```

**Consulta:**
```
Usuario: "¿Cuánto voy hoy?"
→ Retorna resumen del día (en desarrollo)
```

## 📝 Próximos Pasos

Para completar la implementación:

1. **OCR**: Implementar reconocimiento real de patentes en `whatsapp/services/ocr.py`
2. **Integración**: Conectar con modelos de `taller.Documento`, `taller.LineaServicio`, etc.
3. **Evidencia**: Implementar asociación automática de fotos/videos al documento actual
4. **Resumen**: Implementar cálculo real de resumen del día

## 🐛 Troubleshooting

### El webhook no recibe mensajes

1. Verifica que la URL sea HTTPS
2. Verifica que `META_WA_VERIFY_TOKEN` coincida
3. Revisa los logs de Django
4. Verifica los permisos en Meta Developer Console

### "No estás autorizado"

Verifica que el teléfono del remitente coincida con `allowed_operator_phone` en la configuración de la empresa.

### Sesión expirada

La sesión expira después de 30 minutos. Simplemente envía "Nuevo" para comenzar de nuevo.

## 📚 Referencias

- [Meta Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Webhook Setup Guide](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
