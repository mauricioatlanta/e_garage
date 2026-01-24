# Mapeo de Templates para Unificación Visual - eGarage

## Layout Base Unificado
- **Archivo**: `templates/layouts/base_egarage_panel.html`
- **Referencia visual**: `templates/taller/common/servicios/otros_servicios_menu.html`
- **Estructura**: Extiende `base.html` y proporciona bloques estándar para todas las pantallas internas

## Templates Principales a Unificar

### 1. Listados (Listas)
Estas templates deben usar el layout base y mostrar tablas/cards con el mismo estilo visual.

#### Clientes
- [ ] `templates/taller/common/clientes/lista_clientes.html` (COMMON - usar como base)
- [ ] `templates/cl/es/clientes/lista_clientes.html`
- [ ] `templates/us/en/clientes/lista_clientes.html`
- [ ] `templates/us/es/clientes/lista_clientes.html`
- [ ] `templates/mx/es/clientes/lista_clientes.html`
- [ ] `templates/ve/es/clientes/lista_clientes.html`
- [ ] `templates/ec/es/clientes/lista_clientes.html`
- [ ] `templates/co/es/clientes/lista_clientes.html`
- [ ] `templates/pe/es/clientes/lista_clientes.html`
- [ ] `templates/br/es/clientes/lista_clientes.html`

#### Vehículos
- [ ] `templates/us/en/vehiculos/lista_vehiculos.html`
- [ ] `templates/cl/es/vehiculos/lista_vehiculos.html`
- [ ] `templates/us/es/vehiculos/lista_vehiculos.html`
- [ ] `templates/mx/es/vehiculos/lista_vehiculos.html`
- [ ] `templates/ve/es/vehiculos/lista_vehiculos.html`
- [ ] `templates/ec/es/vehiculos/lista_vehiculos.html`
- [ ] `templates/co/es/vehiculos/lista_vehiculos.html`
- [ ] `templates/pe/es/vehiculos/lista_vehiculos.html`
- [ ] `templates/br/es/vehiculos/lista_vehiculos.html`

#### Documentos
- [ ] `templates/taller/common/documentos/lista_documentos.html` (COMMON)
- [ ] `templates/cl/es/documentos/lista_documentos.html`
- [ ] `templates/us/en/documentos/lista_documentos.html`
- [ ] `templates/us/es/documentos/lista_documentos.html`

#### Servicios
- [ ] Templates de listados de servicios (si existen)

#### Repuestos
- [ ] Templates de listados de repuestos (si existen)

---

### 2. Formularios (Crear/Editar)
Estas templates deben usar el layout base y mostrar formularios con el mismo estilo visual.

#### Clientes
- [ ] `templates/taller/common/clientes/crear_cliente.html` (COMMON - usar como base)
- [ ] `templates/cl/es/clientes/crear_cliente.html`
- [ ] `templates/us/en/clientes/crear_cliente.html`
- [ ] `templates/us/es/clientes/crear_cliente.html`
- [ ] `templates/mx/es/clientes/crear_cliente.html`
- [ ] `templates/ve/es/clientes/crear_cliente.html`
- [ ] `templates/ec/es/clientes/crear_cliente.html`
- [ ] `templates/co/es/clientes/crear_cliente.html`
- [ ] `templates/pe/es/clientes/crear_cliente.html`
- [ ] `templates/br/es/clientes/crear_cliente.html`

#### Vehículos
- [ ] `templates/us/es/vehiculos/crear_vehiculo.html`
- [ ] `templates/us/en/vehiculos/crear_vehiculo.html`
- [ ] `templates/cl/es/vehiculos/crear_vehiculo.html`
- [ ] `templates/mx/es/vehiculos/crear_vehiculo.html`
- [ ] `templates/ve/es/vehiculos/crear_vehiculo.html`
- [ ] `templates/ec/es/vehiculos/crear_vehiculo.html`
- [ ] `templates/co/es/vehiculos/crear_vehiculo.html`
- [ ] `templates/pe/es/vehiculos/crear_vehiculo.html`
- [ ] `templates/br/es/vehiculos/crear_vehiculo.html`

#### Documentos
- [ ] `templates/cl/es/documentos/crear_documento.html`
- [ ] `templates/us/en/documentos/crear_documento.html`
- [ ] `templates/us/es/documentos/crear_documento.html`

#### Servicios
- [ ] `templates/us/es/servicios/crear_otro_servicio.html`
- [ ] `templates/us/en/servicios/crear_otro_servicio.html`

---

### 3. Dashboards y Paneles
- [ ] `templates/taller/dashboard/dashboard.html`
- [ ] `templates/portal/dashboard.html`
- [ ] `templates/business_intelligence/dashboard.html`
- [ ] `templates/analytics/dashboard_admin.html`
- [ ] `templates/analytics/dashboard_ai.html`
- [ ] `templates/analytics/dashboard_avanzado.html`
- [ ] `templates/taller/reportes/dashboard.html`
- [ ] `templates/taller/reportes/dashboard_inteligencia.html`
- [ ] `templates/taller/reportes/dashboard_inteligencia_operativa.html`
- [ ] `templates/taller/reportes/dashboard_rentabilidad.html`
- [ ] `templates/taller/common/repuestos/dashboard_repuestos.html`
- [ ] `templates/cl/es/dashboard/dashboard_chile.html`

---

### 4. Configuraciones
- [ ] `templates/settings/company_settings.html`
- [ ] `templates/settings/company_settings_common.html`
- [ ] `templates/settings/company_settings_es.html`
- [ ] Templates en `templates/taller/configuracion/` (si existen)

---

## Estrategia de Implementación

### Paso 1: Actualizar Template de Referencia
1. Actualizar `otros_servicios_menu.html` para usar el nuevo layout (ejemplo de migración)

### Paso 2: Migrar Templates COMMON
1. Migrar las templates en `taller/common/` primero (son la base para los países)
2. Estas servirán como referencia para las versiones por país

### Paso 3: Migrar Templates por País
1. Migrar templates país por país
2. Mantener contenido específico del país (idioma, moneda, etc.)
3. Asegurar que todas usen el mismo layout y estilos

### Paso 4: Verificación
1. Verificar que todas las pantallas se vean igual visualmente
2. Verificar que solo cambien textos/idioma entre países
3. Limpiar estilos inline duplicados
4. Eliminar layouts alternativos obsoletos

---

## Bloques del Layout Base

El layout `base_egarage_panel.html` proporciona los siguientes bloques:

- `{% block page_title %}` - Título principal de la página
- `{% block page_subtitle %}` - Subtítulo o descripción
- `{% block page_icon %}` - Icono emoji para el header (default: 📋)
- `{% block main_actions %}` - Botones de acción principal (crear, exportar, etc.)
- `{% block page_stats %}` - Estadísticas o información adicional en el header
- `{% block search_bar %}` - Barra de búsqueda opcional
- `{% block panel_content %}` - Contenido principal de la página (tablas, formularios, cards, etc.)
- `{% block page_extra_css %}` - CSS adicional específico de la página
- `{% block page_extra_js %}` - JavaScript adicional específico de la página

---

## Notas Importantes

1. **No romper rutas**: Si se cambian nombres de templates, actualizar las vistas relacionadas
2. **Mantener contenido por país**: Solo unificar la estética, no el contenido
3. **Eliminar CSS inline**: Mover estilos generales al layout base o a CSS global
4. **Mantener funcionalidad**: No cambiar la lógica, solo la presentación
5. **Responsive**: Asegurar que el diseño funcione en móvil y desktop

---

**Fecha de creación**: {{ fecha_actual }}
**Última actualización**: {{ fecha_actual }}

