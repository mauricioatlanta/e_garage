# 🔍 DIAGNÓSTICO COMPLETO DE TEMPLATES Y CONTEXT PROCESSORS

## 📋 RESUMEN DE LO IMPLEMENTADO

Se han implementado **5 parches de diagnóstico** para identificar exactamente dónde está el cuello de botella:

1. **Headers de diagnóstico en la vista** - Muestra qué templates físicos está usando Django
2. **Endpoint de debug del Context Processor** - Compara lo que guarda vs lo que ve el CP
3. **Cache bust agresivo** - Fuerza limpieza de caché tras guardar
4. **Bloque CP Snapshot en template** - Muestra variables del CP en la página
5. **Script de verificación de BD** - Confirma que los datos se están guardando

## 🚀 CÓMO USAR LOS DIAGNÓSTICOS

### 1. Headers de Templates (DevTools → Network)

**Paso a paso:**
1. Abre la página de configuración de empresa
2. F12 → pestaña Network
3. Haz cualquier cambio y guarda
4. En la request (GET o POST) → Headers
5. Busca los headers que empiezan con `X-TPL-`

**Qué verás:**
```
X-TPL-base: E:\proyecto\e_garage\templates\common\base.html ✅
X-TPL-common-footer-company: E:\proyecto\e_garage\templates\common\_footer_company.html ✅
X-Settings-Module: gestion_taller.settings
X-TPL-Loader: app_dirs
```

**Si ves algo como:**
```
X-TPL-base: E:\proyecto\e_garage\otra_app\templates\base.html ❌
```
**¡Ese es tu base.html viejo!**

### 2. Endpoint de Debug del Context Processor

**URL:** `/debug/company-header/?empresa_id=4`

**Qué deberías ver:**
```json
{
  "COMPANY_ID": 4,
  "COMPANY_ADDRESS": "Av. Siempre Viva 123",
  "COMPANY_TAX_RATE": "19.00",
  "COMPANY_PHONE": "+56 2 2345 6789",
  "COMPANY_EMAIL": "contacto@empresa.cl",
  "COMPANY_WEBSITE": "www.empresa.cl"
}
```

**Si aquí sale vacío pero en la página de settings sí hay datos:**
- El context processor no está cargado en el settings activo
- O `get_active_empresa` está resolviendo otra empresa
- O el cache del CP no se limpia

### 3. Bloque CP Snapshot en la Página

**Ubicación:** Abajo de todo en la página de configuración

**Qué muestra:**
```
CP Snapshot (esta vista):
ID=4 | ADDRESS=Av. Siempre Viva 123 | PHONE=+56 2 2345 6789 | 
EMAIL=contacto@empresa.cl | WEB=www.empresa.cl | TAX=19.00
```

**Si aquí sale todo con "-":**
- El context processor no está cargado en los settings activos

**Si aquí sale OK pero el footer no:**
- Tu base.html es otro (mira X-TPL-base)

### 4. Script de Verificación de BD

**Ejecutar:**
```bash
python verificar_empresa.py
```

**Confirma que:**
- Los datos se están guardando en BD
- No hay problemas de modelo
- Las empresas existen y tienen configuración

## 🔧 SOLUCIONES COMUNES

### Problema: Template base.html viejo
**Síntoma:** X-TPL-base apunta a otra carpeta
**Solución:** 
1. Buscar y eliminar el base.html duplicado
2. Verificar que `templates_canonical` esté en DIRS
3. Reiniciar el servidor

### Problema: Context Processor no cargado
**Síntoma:** CP Snapshot muestra solo "-"
**Solución:**
1. Verificar que `company_header` esté en `context_processors`
2. Reiniciar el servidor
3. Verificar que estés usando el settings correcto

### Problema: Cached Loader
**Síntoma:** X-TPL-Loader = "cached"
**Solución:**
1. Comentar `loaders` en TEMPLATES[0]['OPTIONS']
2. O setear `DEBUG=True` en desarrollo
3. Reiniciar el servidor

### Problema: Cache del Context Processor
**Síntoma:** Cambios no se reflejan aunque se guarden
**Solución:**
1. El parche ya incluye `cache.clear()` temporal
2. Usar el botón "REFRESH SYSTEM" en la página
3. O llamar manualmente a `/debug/company-header/`

## 📊 FLUJO DE DIAGNÓSTICO

```
1. Abrir página de configuración
   ↓
2. Verificar CP Snapshot (¿variables vacías?)
   ↓
3. Si vacías → Context Processor no cargado
   ↓
4. Si OK → Verificar X-TPL-base (¿base correcto?)
   ↓
5. Si base correcto → Verificar X-TPL-Loader (¿cached?)
   ↓
6. Si no cached → Verificar endpoint debug (¿CP devuelve datos?)
   ↓
7. Si CP OK → Problema en template del footer
   ↓
8. Si CP no OK → Problema en get_active_empresa o cache
```

## 🎯 QUÉ ESPERAR TRAS LOS PARCHES

**En DevTools/Headers verás:**
- X-TPL-base apuntando a una ruta exacta
- X-Settings-Module confirmando el settings activo
- X-TPL-Loader = "app_dirs" (sin caché)

**En /debug/company-header/ verás:**
- JSON con todos los datos del context processor
- Confirmación de que el CP está funcionando

**En el bloque CP Snapshot verás:**
- Variables del CP aunque el base no las incluya
- Confirmación de que el CP está cargado

## 🚨 SI NADA SE MUEVE

Pega aquí los valores de:
- X-TPL-base
- X-TPL-common-footer-company  
- X-Settings-Module
- X-TPL-Loader
- Salida JSON de /debug/company-header/?empresa_id=...

**Lo normal es que al ver X-TPL-base descubras que estás extendiendo un base.html obsoleto en otra app/carpeta.**

Una vez apuntes al base correcto o reinicies sin caché, el footer y el IVA se van a reflejar de inmediato.

---

## 📝 NOTAS TÉCNICAS

- **Cache bust:** Se implementó `cache.clear()` temporal solo para depurar
- **Headers:** Se añadieron 5 headers de diagnóstico en cada respuesta
- **Endpoint debug:** Requiere login y permisos de taller
- **Script BD:** Independiente de Django, solo para verificación rápida

## 🔄 PRÓXIMOS PASOS

1. **Probar los headers** en DevTools
2. **Verificar el endpoint** de debug
3. **Comparar CP Snapshot** con footer
4. **Ejecutar script** de verificación
5. **Identificar el cuello de botella** específico
6. **Aplicar la solución** correspondiente
