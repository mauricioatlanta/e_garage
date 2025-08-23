# Reglas de Negocio y Feature Flags

## Feature flags
- enable_servicios / enable_repuestos
- single_owner_mode
- dividir_por_tecnico_por_defecto

## Validaciones
- Documento.clean(): empresa consistente en todas las FKs.
- Auditoría: AuditMixin (created_by, updated_by).
- Permisos: solo staff/admin puede editar ConfiguraciónEmpresa.

## Flujos por tipo de empresa
- Taller: muestra servicios, técnicos, dashboards de órdenes.
- Casa de repuestos: muestra repuestos, oculta servicios.

## Errores típicos y buenas prácticas
- Usar solo fecha_emision para KPIs y reportes.
- Evitar ._meta top-level salvo para introspección avanzada.
- FKs siempre con rutas string ('app.Model').
