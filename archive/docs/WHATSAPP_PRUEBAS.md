# 🧪 eGarage Air - Pruebas de Fuego

Este documento describe las 3 pruebas críticas que debes realizar para verificar que el sistema funciona correctamente.

## 📋 Prerequisitos

1. ✅ Migraciones ejecutadas: `python manage.py migrate whatsapp`
2. ✅ Variables de entorno configuradas en `.env`
3. ✅ Empresa configurada en Admin con `phone_number_id` y `allowed_operator_phone`
4. ✅ Webhook configurado en Meta Developer Console
5. ✅ API keys configuradas (OpenAI o Gemini)

## 🔥 Prueba 1: Jerga de Taller

### Objetivo
Verificar que el sistema entiende jerga coloquial y convierte precios correctamente.

### Pasos

1. Envía un **audio** o **texto** diciendo:
   ```
   "Cámbiame las balatas al Corsa, cobrale 40 lucas"
   ```

2. **Resultado Esperado:**
   - ✅ El sistema transcribe el audio (si es audio)
   - ✅ Extrae: servicio "Cambio de balatas", precio 40000
   - ✅ Muestra confirmación con los datos extraídos
   - ✅ Confidence >= 0.70

### Verificación

El mensaje de respuesta debe incluir:
```
✅ Servicios agregados:

• Cambio de balatas: $40,000
```

### Si Falla

- Verifica que `OPENAI_API_KEY` o `GEMINI_API_KEY` esté configurado
- Revisa los logs de Django para ver errores de API
- Verifica que el modelo de IA esté disponible

---

## 🔥 Prueba 2: Modo Manual (Confianza Baja)

### Objetivo
Verificar que cuando la IA no tiene suficiente confianza, se activa el modo manual.

### Pasos

1. Envía un **audio con mucho ruido de fondo** (herramientas, música, etc.) o un mensaje muy ambiguo:
   ```
   [Audio con ruido] "mmm... algo... no sé... tal vez..."
   ```

2. **Resultado Esperado:**
   - ✅ El sistema procesa el audio/texto
   - ✅ Detecta confidence < 0.70
   - ✅ Muestra botones interactivos:
     - 🛠 Agregar Servicio
     - 🔩 Agregar Repuesto
     - 🏢 Servicio Externo
     - ❌ Cancelar

### Verificación

Debes ver un mensaje como:
```
⚠️ No pude entender el mensaje con suficiente confianza.

Por favor, selecciona una opción:
[Botones interactivos]
```

### Si Falla

- Verifica que el umbral de confidence (0.70) esté funcionando
- Revisa que los botones interactivos se envíen correctamente
- Verifica logs para ver el confidence calculado

---

## 🔥 Prueba 3: Resumen del Día

### Objetivo
Verificar que el sistema responde a consultas de resumen.

### Pasos

1. Envía un mensaje de texto:
   ```
   "¿Cuánto voy hoy?"
   ```
   o
   ```
   "¿Cuánto llevo ganado?"
   ```

2. **Resultado Esperado:**
   - ✅ El sistema identifica acción `GET_SUMMARY`
   - ✅ Muestra mensaje de resumen (actualmente en desarrollo)
   - ✅ Confidence = 1.0 (consulta clara)

### Verificación

Debes ver un mensaje como:
```
📊 Resumen del día

⚠️ Funcionalidad en desarrollo

Próximamente podrás ver:
• Total de OTs del día
• Ingresos totales
• Servicios realizados
```

### Nota

Esta funcionalidad está marcada como "en desarrollo" porque requiere:
- Integración con modelos de `taller.Documento`
- Cálculo de totales del día
- Filtrado por empresa y fecha

---

## 🐛 Troubleshooting General

### El sistema no responde

1. Verifica que el webhook esté configurado correctamente en Meta
2. Revisa los logs de Django: `tail -f logs/django.log`
3. Verifica que `META_WA_VERIFY_TOKEN` coincida
4. Asegúrate de que el teléfono coincida con `allowed_operator_phone`

### Error "No estás autorizado"

- Verifica que el teléfono del remitente coincida exactamente con `allowed_operator_phone` en Admin
- Formato esperado: `56912345678` (sin +, sin espacios)

### Error de API de IA

- Verifica que las API keys estén correctas
- Revisa los límites de uso de tu cuenta (OpenAI/Gemini)
- Verifica que tengas créditos disponibles
- Revisa los logs para ver el error específico

### Audio no se transcribe

- Verifica que `OPENAI_API_KEY` esté configurado (Whisper requiere OpenAI)
- Verifica que el formato de audio sea compatible (OGG, MP3, etc.)
- Revisa los logs para ver errores de transcripción

### JSON inválido de la IA

- El sistema intenta limpiar la respuesta automáticamente
- Si persiste, verifica que el modelo esté configurado para devolver JSON
- Revisa los logs para ver la respuesta cruda de la IA

---

## 📊 Logs Útiles

Para monitorear el sistema en tiempo real:

```bash
# Ver logs de Django
tail -f logs/django.log

# Filtrar solo mensajes de WhatsApp
tail -f logs/django.log | grep whatsapp

# Filtrar errores
tail -f logs/django.log | grep ERROR
```

---

## ✅ Checklist de Pruebas

- [ ] Prueba 1: Jerga de Taller - ✅ Pasó
- [ ] Prueba 2: Modo Manual - ✅ Pasó
- [ ] Prueba 3: Resumen del Día - ✅ Pasó
- [ ] Webhook responde correctamente
- [ ] Validación de operador funciona
- [ ] Sesiones expiran correctamente (30 min)
- [ ] Botones interactivos se muestran
- [ ] Transcripción de audio funciona
- [ ] Procesamiento de texto funciona
- [ ] Manejo de errores funciona

---

## 🎯 Próximos Pasos Después de las Pruebas

Una vez que las 3 pruebas pasen:

1. **Integración Real**: Conectar con `taller.Documento` y crear OTs reales
2. **OCR de Patentes**: Implementar reconocimiento real de patentes
3. **Resumen del Día**: Calcular totales reales desde la base de datos
4. **Evidencia**: Asociar fotos/videos automáticamente al documento
5. **Notificaciones**: Enviar confirmaciones al cliente cuando se finalice la OT

---

¡Felicidades! Si todas las pruebas pasan, eGarage Air está listo para producción. 🚀
