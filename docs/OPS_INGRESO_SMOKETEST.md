# Smoke test – Centro de Ingreso Pro (ops/ingreso)

## Objetivo

Verificar el flujo completo del Centro de Ingreso sin fallos críticos.

## Precondiciones

- Usuario autenticado con empresa asignada (staff/técnico/admin).
- Ruta base Chile: `/cl/es/ops/ingreso/` o USA: `/us/ops/ingreso/`.

## Pasos (manual)

1. **Entrar a ingreso**
   - Ir al Centro de Operaciones (espacial).
   - Pulsar el card **"INGRESO VEHÍCULO"** (recepción inteligente con evidencia).
   - Comprobar que carga `/.../ops/ingreso/` con opciones: Escanear patente (si OCR disponible) y Escribir patente.

2. **Patente inexistente → crear cliente → crear vehículo**
   - Escribir una patente que no exista (ej. `TEST99`).
   - Enviar (Buscar/Continuar).
   - Debe mostrarse el panel "Vehículo no encontrado" con formulario de creación rápida (patente fija, cliente, opcional marca/modelo, año).
   - Opcional: seguir el enlace "Crear cliente", crear cliente, volver con `next=.../ops/ingreso/vehiculo/crear/?patente=TEST99` y que el cliente quede preseleccionado.
   - Completar el formulario (cliente, año obligatorio) y pulsar "Crear ahora".
   - Debe redirigir a paso **Kilometraje** para ese vehículo.

3. **Kilometraje + omitir foto con motivo**
   - En el paso Kilometraje, ingresar un valor (ej. 50000).
   - No subir foto; en "Motivo si omite foto" escribir: "Tablero no visible".
   - Enviar.
   - Debe crearse `RegistroKilometraje` y redirigir a **Documento**.

4. **Crear documento OT**
   - En motivo escribir "Revisión frenos"; tipo **Orden de Trabajo**.
   - Pulsar "Crear documento".
   - Debe crearse un `Documento` en estado BORRADOR y redirigir a **Checklist**.

5. **Checklist: combustible + daño**
   - Ajustar nivel de combustible (slider).
   - Subir al menos una foto de ángulo si se desea (opcional).
   - En el esquema 2D, tocar una zona (ej. front_left), en el modal elegir tipo (rayón), nota opcional, severidad 1, Guardar marca.
   - Pulsar "Continuar".
   - Debe redirigir a **Repuestos**.

6. **Agregar repuesto manual y comprobar LineaRepuesto**
   - En la pestaña Manual: buscar por código o nombre (o agregar libre: código, nombre, cantidad, precio).
   - Pulsar "Agregar línea" o elegir un resultado de búsqueda.
   - Comprobar que se crea una línea en la tabla y que existe `LineaRepuesto` para el documento (en admin o BD).

7. **Misma patente de nuevo → debe ir a kilometraje**
   - Volver al inicio de ingreso (home) y escribir la misma patente usada antes (ej. `TEST99`).
   - Enviar.
   - Debe detectarse el vehículo existente y redirigir directamente a **Kilometraje** (sin pantalla de creación).

## Notas

- Si EasyOCR no está instalado, el botón de escanear patente debe indicar "OCR no disponible" y el flujo manual debe funcionar igual.
- Todas las vistas y APIs deben filtrar por `empresa` del usuario.
- Errores esperables: 404 si documento/vehículo no pertenece a la empresa; mensajes claros en UI, no "Error 500".
