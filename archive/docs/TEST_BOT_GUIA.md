# 🤖 Guía de Uso del Simulador de WhatsApp

## 🚀 Inicio Rápido

### 1. Configurar Phone Number ID

Antes de usar el simulador, debes configurar el `PHONE_NUMBER_ID`:

**Opción A: Editar `test_bot.py`**
```python
PHONE_NUMBER_ID = "tu_phone_number_id_real_aqui"
```

**Opción B: Usar el menú del simulador**
- Ejecuta `python test_bot.py`
- Selecciona opción `6` para configurar

### 2. Iniciar el Servidor Django

En una terminal:
```bash
python manage.py runserver
```

### 3. Ejecutar el Simulador

En otra terminal:
```bash
python test_bot.py
```

## 📋 Secuencia de Prueba Recomendada

### Prueba Básica del Flujo

1. **Iniciar sesión**: Escribe `Nuevo` o `🆕`
   - ✅ Debería responder: "📸 *Nuevo Vehículo*\n\nEnvía una foto de la patente para comenzar."

2. **Enviar patente**: Opción 2 (Imagen)
   - ✅ Debería detectar patente (si OCR está implementado) o pedir otra foto

3. **Enviar kilometraje**: Escribe `50000`
   - ✅ Debería mostrar menú de botones interactivos

4. **Seleccionar acción**: Opción 4 → `servicio`
   - ✅ Debería pedir detalles del servicio

5. **Agregar servicio**: Escribe `Cambio de aceite, 50 lucas`
   - ✅ Debería procesar con NLP y extraer: servicio "Cambio de aceite", precio 40000

### Prueba de NLP

**Prueba de Jerga:**
```
Mensaje: "Cámbiame las balatas al Corsa, cobrale 40 lucas"
Resultado esperado: Servicio "Cambio de balatas" con precio 40000
```

**Prueba de Audio:**
- Opción 3 (Enviar audio)
- El sistema debería transcribir y procesar (si OpenAI está configurado)

**Prueba de Modo Manual:**
```
Mensaje: "asdfghjkl" (texto sin sentido)
Resultado esperado: Botones de modo manual (confidence < 0.70)
```

## 🔍 Qué Observar en los Logs

Mientras usas el simulador, revisa la terminal donde corre `runserver`:

### Logs Esperados

```
INFO - Mensaje recibido: {...}
INFO - Sesión recuperada para 56912345678
INFO - Estado actual: WAITING_PLATE
INFO - Procesando acción NLP: ADD_SERVICE (confidence: 0.95)
INFO - Respuesta parseada correctamente: action=ADD_SERVICE, confidence=0.95
```

### Errores Comunes

**Error 403:**
- Verifica que `PHONE_TEST` coincida con `allowed_operator_phone` en Admin
- Verifica que `PHONE_NUMBER_ID` coincida con el configurado en Admin

**Error 404:**
- Verifica que la URL sea `http://127.0.0.1:8000/whatsapp/webhook/`
- Verifica que el servidor esté corriendo

**Error de conexión:**
- Asegúrate de que `runserver` esté corriendo
- Verifica que el puerto 8000 esté disponible

## 🎯 Comandos Útiles

### Secuencia Rápida

El simulador incluye una opción `5` que ejecuta una secuencia completa de pruebas automáticamente.

### Pruebas Específicas

**Probar creación de OT:**
```
1. Nuevo
2. [Imagen]
3. 50000
4. [Botón: servicio]
5. "Abre una orden para el Toyota patente ABCD12 de Don Juan, por un cambio de aceite"
```

**Probar resumen:**
```
1. Nuevo
2. [Imagen]
3. 50000
4. "¿Cuánto voy hoy?"
```

## 🐛 Troubleshooting

### El simulador no se conecta

1. Verifica que el servidor Django esté corriendo
2. Verifica la URL en `test_bot.py`
3. Verifica que no haya firewall bloqueando

### El bot no responde

1. Revisa los logs de Django para ver errores
2. Verifica que la empresa esté configurada en Admin
3. Verifica que `phone_number_id` y `allowed_operator_phone` coincidan

### NLP no funciona

1. Verifica que `OPENAI_API_KEY` o `GEMINI_API_KEY` esté configurado
2. Revisa los logs para ver errores de API
3. Verifica que tengas créditos disponibles en tu cuenta de IA

### OCR no funciona

1. El OCR está marcado como "en desarrollo"
2. Por ahora, puedes simular enviando la patente como texto después de la imagen

## 💡 Tips

- Usa la opción `5` (Secuencia rápida) para probar el flujo completo rápidamente
- Revisa siempre los logs de Django para ver qué está pasando
- Si algo falla, verifica primero que la configuración en Admin sea correcta
- El simulador es perfecto para desarrollar sin necesidad de Meta Cloud API

## 📝 Notas

- El simulador NO requiere configuración de Meta
- El simulador NO requiere ngrok
- El simulador funciona completamente offline (excepto NLP que necesita API keys)
- Los mensajes se procesan igual que si vinieran de Meta real

---

¡Disfruta probando eGarage Air! 🚀
