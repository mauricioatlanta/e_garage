# eGarage Knowledge Pack

## 1. Misión, usuarios y países (Chile/USA)
Sistema multi-tenant para talleres y casas de repuestos, operando en Chile (CLP, IVA 19%) y USA (USD, sales tax). Usuarios: administradores, técnicos/vendedores, staff, clientes. Soporta flujos y reglas específicas para cada país.

## 2. Entidades y relaciones (resumen)
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

## 3. Flujos críticos
- Creación documento: login → selección empresa → crear documento (fecha_emision, técnico) → agregar líneas (hereda responsable si flag OFF).
- Herencia a líneas: si “dividir por técnico/vendedor” está OFF, las líneas heredan responsable del documento.
- Dashboards: métricas por técnico/vendedor, ventas, servicios, repuestos.

## 4. Configuración por empresa
- Logo, IVA/sales tax, moneda, feature flags, branding, defaults.
- Permisos: solo staff/admin puede editar ConfiguraciónEmpresa.

## 5. Validaciones y permisos
- Documento.clean(): empresa consistente en todas las FKs.
- AuditMixin: auditoría created_by/updated_by.
- FKs siempre con rutas string ('app.Model').

## 6. Consultas ORM patrón
- KPIs: ExpressionWrapper(F('cantidad')*F('precio_unitario'))
- Coalesce(mecanico, documento__tecnico_responsable) para métricas.
- Usar solo fecha_emision para KPIs y reportes.

## 7. KPIs (vendedor/técnico efectivo)
- Técnicos/vendedores efectivos por mes, ventas por técnico, servicios realizados, repuestos vendidos.

## 8. Errores típicos y cómo evitarlos
- "No changes detected" en makemigrations: revisar apps y modelos.
- ContentTypes: limpiar si hay modelos legacy.
- Alias: Mecanico → Tecnico (solo uno en sistema).
- Evitar ._meta top-level salvo para introspección avanzada.

## 9. Checklist de operación
- makemigrations / migrate
- backfill_responsables (dry-run y real)
- ruff, isort, black (lint/format)
- smoke test: login, crear documento, dashboard
- KPIs: técnicos/vendedores efectivos, ventas por mes

## 10. Glosario (es/en)
- Empresa: Company
- Tecnico: Technician/Salesperson
- Documento: Document
- LineaRepuesto: SparePartLine
- LineaServicio: ServiceLine
- LineaOtroServicio: OutsourcedServiceLine
- Cliente: Client/Customer
- Vehiculo: Vehicle
- ConfiguracionEmpresa: CompanySettings
- AuditMixin: AuditMixin
- fecha_emision: issue_date
- responsable: responsible
- subtotal: subtotal
- ganancia: profit
- IVA: VAT
- sales tax: sales tax
- CLP: Chilean Peso
- USD: US Dollar
