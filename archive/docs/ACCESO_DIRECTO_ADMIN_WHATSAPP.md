# 🔗 Acceso Directo al Admin de WhatsApp

## Problema

No encuentras la opción de WhatsApp en el menú del admin.

## Solución Rápida: Acceso Directo

Mientras se soluciona el problema del menú, puedes acceder directamente a las URLs:

### Configuración de WhatsApp
```
http://127.0.0.1:8000/admin/whatsapp/empresawhatsappconfig/
```

### Sesiones de WhatsApp
```
http://127.0.0.1:8000/admin/whatsapp/whatsappsession/
```

### Agregar Nueva Configuración
```
http://127.0.0.1:8000/admin/whatsapp/empresawhatsappconfig/add/
```

## Pasos para Configurar

1. **Abre la URL de agregar configuración:**
   ```
   http://127.0.0.1:8000/admin/whatsapp/empresawhatsappconfig/add/
   ```

2. **Completa el formulario:**
   - **Empresa**: Selecciona una empresa del dropdown
   - **Phone number id**: `test_123`
   - **Allowed operator phone**: `56912345678`
   - **Is enabled**: ✅ Marcado
   - **Enable audio**: ✅ Marcado
   - **Enable ocr**: ✅ Marcado

3. **Guarda**

## Solución Permanente

El problema es que el admin no se importa automáticamente. He actualizado `whatsapp/apps.py` para solucionarlo.

**Para que surta efecto:**

1. **Reinicia el servidor Django:**
   ```bash
   # Detén el servidor (Ctrl+C en la terminal donde corre)
   # Luego vuelve a iniciarlo:
   python manage.py runserver
   ```

2. **Después de reiniciar, deberías ver "WhatsApp" en el menú del admin**

## Verificación

Después de reiniciar, verifica:

1. Ve a: `http://127.0.0.1:8000/admin/`
2. Deberías ver en el menú lateral: **"eGarage Air (WhatsApp)"** o **"WhatsApp"**

## Si Aún No Aparece

Usa el acceso directo de arriba. Funciona igual de bien.

---

**Nota:** El acceso directo funciona siempre, incluso si el menú no aparece.
