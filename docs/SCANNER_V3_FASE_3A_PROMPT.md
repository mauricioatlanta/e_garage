# Prompt para Cursor — Implementar Fase 3A del Scanner Desarme

Copia el siguiente bloque en Cursor para implementar la Fase 3A según el documento **Scanner Desarme v3 — PUM definitivo** (`docs/SCANNER_DESARME_V3_PUM.md`).

---

## Prompt

```
Implementar Fase 3A del módulo Scanner Desarme según el documento "Scanner Desarme v3 — PUM definitivo".

Objetivo:
Agregar inteligencia operativa al scanner sin romper el flujo actual.

NO rediseñar la UI completa.
Extender lo que ya existe.

Cambios requeridos:

1. ENDPOINT BULK PRECIO

Crear endpoint:

POST /api/piezas/bulk-precio/

Payload:
{
  "ids": [1,2,3],
  "factor": 1.1
}

Reglas:
- máximo 100 ids
- validar empresa del usuario
- actualizar precio_venta_sugerido *= factor
- devolver { success: true }

2. FILTRO PENDIENTES

Agregar filtro frontend:

Pendiente =
precio_venta_sugerido == 0
OR
precio_venta_sugerido == null

y estado in (DISPONIBLE, RESERVADA)

Mostrar solo esas piezas.

3. PANEL COMERCIAL MEJORADO

Calcular en frontend:

valor_potencial =
sum(precio_venta_sugerido)
for piezas estado DISPONIBLE or RESERVADA

valor_perdido_danadas =
sum(precio_venta_sugerido)
for piezas estado DANADA

Top 5 piezas más valiosas.

Actualizar al ejecutar refreshLiveMetrics().

4. REAJUSTE PRECIO POR ZONA

En cada bloque de zona agregar botones:

+10%
-10%

Implementación:
obtener ids de piezas visibles de esa zona
llamar bulk-precio endpoint.

5. FILTRO PRIORIDAD

Si campo prioridad existe:

mostrar bloque:

⭐ Piezas prioritarias

6. MANTENER

- i18n
- country_url
- modo revisión rápida
- filtros existentes
- compatibilidad backend actual

7. ENTREGABLE

Listar:
- archivos modificados
- endpoints nuevos
- funciones JS agregadas
- cualquier mejora sugerida para Fase 3B
```

---

## Referencia rápida

- **Especificación completa:** `docs/SCANNER_DESARME_V3_PUM.md`
- **Definiciones implementables:** secciones A–E al inicio del doc (estados, sin precio, bulk limit, heurística revisión, orden cards).
- **Checklist técnico:** al final del doc (backend + frontend).
- **Nota:** Parte de la Fase 3A ya está implementada (bulk-precio, filtro Pendientes, panel comercial con valor perdido daño, botones +10%/−10% por zona). Usar este prompt para revisar cobertura o para que otro desarrollador replique en otro entorno.
