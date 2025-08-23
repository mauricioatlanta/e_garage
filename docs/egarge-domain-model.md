# Modelo de Dominio eGarage

## Modelos clave
- Empresa: nombre, país, moneda, settings.
- Tecnico: FK empresa, nombre, activo, único para técnicos/vendedores.
- Documento: fecha_emision, tecnico_responsable (FK Tecnico, nullable), empresa, cliente, vehiculo, tipo, estado.
- LineaRepuesto: FK documento, repuesto, nombre, cantidad, precio_unitario, descuento, subtotal, related_name='lineas_repuesto'.
- LineaServicio: FK documento, servicio, nombre, cantidad, precio_unitario, descuento, subtotal, related_name='lineas_servicio'.
- LineaOtroServicio: FK documento, servicio, nombre, empresa_externa, cantidad, costo_interno, precio_cliente, ganancia, related_name='lineas_otro_servicio'.
- Cliente: empresa, nombre, rut/ein, contacto.
- Vehiculo: empresa, cliente, patente/vin, marca, modelo.
- ConfiguracionEmpresa: logo, IVA/sales tax, moneda, flags, branding.
- AuditMixin: created_by, updated_by, timestamps.

## Índices e invariantes
- Índices en Documento (empresa, fecha_emision), líneas (documento, servicio/repuesto), Cliente (empresa).
- Invariantes: validación de empresa/tenant en clean(), herencia de responsable a líneas si flag OFF, solo usar fecha_emision.

## Related_name
- Documento.lineas_repuesto, Documento.lineas_servicio, Documento.lineas_otro_servicio.

## Queries representativas
- KPIs: ExpressionWrapper(F('cantidad')*F('precio_unitario'))
- Coalesce(mecanico, documento__tecnico_responsable) para métricas.
