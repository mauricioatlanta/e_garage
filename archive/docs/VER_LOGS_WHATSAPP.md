# 📊 Cómo Observar los Logs de Django - eGarage Air

## 🖥️ Método 1: Logs en Tiempo Real (Terminal) - RECOMENDADO

### Paso 1: Iniciar el Servidor

En una terminal, ejecuta:
```bash
python manage.py runserver
```

**Los logs aparecerán directamente en esta terminal** mientras el servidor está corriendo.

### Paso 2: Ejecutar el Simulador

En otra terminal, ejecuta:
```bash
python test_bot.py
```

### Paso 3: Observar los Logs

Mientras usas el simulador, verás en la terminal del servidor mensajes como:

```
2026-01-01 12:00:00 INFO whatsapp.views Mensaje recibido: {...}
2026-01-01 12:00:01 INFO whatsapp.services.flow Procesando mensaje de 56912345678
2026-01-01 12:00:02 INFO whatsapp.services.flow Estado actual: WAITING_PLATE
2026-01-01 12:00:03 DEBUG whatsapp.services.nlp OpenAI respuesta recibida: {...}
```

## 🔍 Método 2: Filtrador de Logs (Solo WhatsApp)

### Usar el Script Helper

He creado un script que filtra y muestra solo los logs relevantes de WhatsApp:

```bash
python watch_whatsapp_logs.py
```

Este script:
- ✅ Muestra solo logs de WhatsApp
- ✅ Colorea los logs según su nivel (ERROR=rojo, WARNING=amarillo, INFO=verde)
- ✅ Filtra automáticamente información relevante
- ✅ Muestra requests al webhook

## 📁 Método 3: Logs en Archivo (Si está configurado)

Si tienes logging a archivo configurado, los logs estarán en `logs/django.log`:

### Windows (PowerShell):
```powershell
# Ver logs en tiempo real
Get-Content logs\django.log -Wait -Tail 50

# Ver últimas 100 líneas
Get-Content logs\django.log -Tail 100

# Filtrar solo logs de WhatsApp
Get-Content logs\django.log -Wait -Tail 50 | Select-String -Pattern "whatsapp"
```

### Linux/Mac:
```bash
# Ver logs en tiempo real
tail -f logs/django.log

# Ver últimas 100 líneas
tail -n 100 logs/django.log

# Filtrar solo logs de WhatsApp
tail -f logs/django.log | grep -i whatsapp
```

## 📋 Qué Buscar en los Logs

### Logs Normales (INFO) - Verde

```
INFO whatsapp.views Mensaje recibido: {...}
INFO whatsapp.views Sesión recuperada para 56912345678
INFO whatsapp.services.flow Estado actual: WAITING_PLATE
INFO whatsapp.services.flow Procesando acción NLP: ADD_SERVICE (confidence: 0.95)
INFO whatsapp.services.meta Mensaje enviado a 56912345678
```

### Logs de Debug (DEBUG) - Cyan

```
DEBUG whatsapp.services.nlp OpenAI respuesta recibida: {...}
DEBUG whatsapp.services.nlp Respuesta parseada correctamente: action=ADD_SERVICE
DEBUG whatsapp.services.flow Contexto actualizado: {'patente': 'ABCD12', ...}
```

### Logs de Error (ERROR) - Rojo

```
ERROR whatsapp.services.nlp Error llamando OpenAI: Connection timeout
ERROR whatsapp.views Error procesando mensaje: ...
```

### Logs de Advertencia (WARNING) - Amarillo

```
WARNING whatsapp.views Teléfono no autorizado: 56999999999
WARNING whatsapp.services.nlp Confianza baja (0.65), requiere modo manual
WARNING whatsapp.services.flow Sesión expirada
```

## 🎯 Logs Específicos de eGarage Air

### Flujo Conversacional

```
# Inicio de sesión
INFO whatsapp.services.flow Estado: IDLE -> WAITING_PLATE

# Procesamiento de patente
INFO whatsapp.services.ocr Patente detectada: ABCD12
INFO whatsapp.services.flow Estado: WAITING_PLATE -> WAITING_MILEAGE

# Procesamiento de kilometraje
INFO whatsapp.services.flow Estado: WAITING_MILEAGE -> WAITING_ACTION

# Procesamiento NLP
INFO whatsapp.services.nlp Procesando texto: "Cambio de aceite, 50 lucas"
INFO whatsapp.services.nlp OpenAI respuesta recibida: {"action": "ADD_SERVICE", ...}
INFO whatsapp.services.flow Procesando acción NLP: ADD_SERVICE (confidence: 0.95)
```

### NLP y IA

```
# Transcripción de audio
INFO whatsapp.services.nlp Audio transcrito: Cambio de aceite, 50 lucas...

# Procesamiento de texto
INFO whatsapp.services.nlp OpenAI respuesta recibida: {...}
INFO whatsapp.services.nlp Respuesta parseada correctamente: action=ADD_SERVICE, confidence=0.95

# Modo manual (confidence bajo)
WARNING whatsapp.services.nlp Confianza baja (0.65), requiere modo manual
```

### Requests al Webhook

```
[01/Jan/2026 12:00:00] "POST /whatsapp/webhook/ HTTP/1.1" 200 0
[01/Jan/2026 12:00:01] "GET /whatsapp/webhook/?hub.mode=subscribe&... HTTP/1.1" 200 5
```

## 🛠️ Mejorar Visibilidad de Logs

### Activar Debug Mode

En `gestion_taller/settings.py`, asegúrate de que:
```python
DEBUG = True  # Para ver logs detallados
```

### Configuración Actual

Los logs de WhatsApp están configurados para mostrar:
- **DEBUG** cuando `DEBUG = True` (modo desarrollo)
- **INFO** cuando `DEBUG = False` (modo producción)

La configuración actual en `settings.py` incluye:
- Logger específico para `whatsapp` con nivel DEBUG en desarrollo
- Formato verbose con timestamp y nombre del módulo
- Salida a consola (terminal)

## 📝 Ejemplo de Sesión Completa

```
[Terminal del Servidor Django]

2026-01-01 12:00:00 INFO whatsapp.views Mensaje recibido: {"object": "whatsapp_business_account", ...}
2026-01-01 12:00:00 INFO whatsapp.views Configuración encontrada para phone_number_id: TU_ID_EN_ADMIN
2026-01-01 12:00:00 INFO whatsapp.views Sesión recuperada para 56912345678
2026-01-01 12:00:01 INFO whatsapp.services.flow Procesando mensaje de 56912345678
2026-01-01 12:00:01 INFO whatsapp.services.flow Estado actual: IDLE
2026-01-01 12:00:01 INFO whatsapp.services.flow Estado: IDLE -> WAITING_PLATE
2026-01-01 12:00:02 INFO whatsapp.services.meta Mensaje enviado a 56912345678
[01/Jan/2026 12:00:02] "POST /whatsapp/webhook/ HTTP/1.1" 200 0
```

## 💡 Tips y Trucos

### 1. Usar Dos Terminales
- **Terminal 1**: `python manage.py runserver` (verás los logs aquí)
- **Terminal 2**: `python test_bot.py` (envías mensajes desde aquí)

### 2. Filtrar Logs en Tiempo Real

**Windows (PowerShell):**
```powershell
python manage.py runserver | Select-String -Pattern "whatsapp|INFO|ERROR"
```

**Linux/Mac:**
```bash
python manage.py runserver | grep -E "whatsapp|INFO|ERROR"
```

### 3. Buscar Errores Rápidamente

Busca líneas que contengan:
- `ERROR` - Errores críticos
- `WARNING` - Advertencias (confianza baja, sesión expirada, etc.)
- `Estado actual` - Para ver el flujo de estados
- `confidence` - Para ver la confianza del NLP

### 4. Observar Cambios de Estado

Los logs mostrarán:
```
Estado: IDLE -> WAITING_PLATE
Estado: WAITING_PLATE -> WAITING_MILEAGE
Estado: WAITING_MILEAGE -> WAITING_ACTION
```

### 5. Ver Respuestas de la IA

Busca:
```
OpenAI respuesta recibida: {...}
Gemini respuesta recibida: {...}
Respuesta parseada correctamente: action=...
```

## 🐛 Troubleshooting

### No Veo Logs

1. **Verifica DEBUG mode:**
   ```python
   # En gestion_taller/settings.py
   DEBUG = True
   ```

2. **Verifica que el logger esté configurado:**
   - Debería haber un logger para `whatsapp` en `LOGGING`

3. **Verifica que uses logger en el código:**
   - El código usa `logger.info()`, `logger.debug()`, etc.

4. **Prueba con print() temporalmente:**
   ```python
   print("DEBUG: Esto debería verse")
   ```

### Logs Muy Verbosos

Si ves demasiados logs de Django, puedes:
- Filtrar solo logs de WhatsApp usando el script `watch_whatsapp_logs.py`
- O ajustar el nivel de logging en settings

### No Veo Logs de WhatsApp

1. Verifica que la app `whatsapp` esté en `INSTALLED_APPS`
2. Verifica que el logger esté configurado en `LOGGING`
3. Verifica que `DEBUG = True` para ver logs DEBUG

## 🎯 Comandos Rápidos

```bash
# Ver logs en tiempo real (Windows)
python manage.py runserver

# Ver logs filtrados (Windows)
python watch_whatsapp_logs.py

# Ver logs desde archivo (Windows)
Get-Content logs\django.log -Wait -Tail 50 | Select-String -Pattern "whatsapp"

# Ver logs en tiempo real (Linux/Mac)
python manage.py runserver | grep -i whatsapp

# Ver logs filtrados (Linux/Mac)
python watch_whatsapp_logs.py
```

---

**¡Ahora puedes observar todo lo que pasa en eGarage Air en tiempo real!** 🚀
