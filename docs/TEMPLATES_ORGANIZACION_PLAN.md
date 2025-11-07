# Plan de Organización de Templates - eGarage

## Fecha: 27 de Octubre, 2025

## 1. ESTADO ACTUAL

### Estructura de Carpetas de Templates

#### A. Carpeta Principal: `/templates/`
Contiene **276 archivos** organizados en:

**Módulos de Autenticación y Cuenta:**
- `account/` - Login, signup, password reset, email confirmation (19 archivos)
- `auth/` - Login alternativo (1 archivo)
- `registration/` - Password reset forms (6 archivos)

**Módulos Administrativos:**
- `admin/` - Dashboard de suscripciones admin (1 archivo)
- `admin_panel/` - Panel de administración (1 archivo)
- `analytics/` - Dashboards de analítica (4 archivos)
- `business_intelligence/` - BI dashboard (1 archivo)

**Módulos de la Aplicación Taller:**
- `taller/` - **176 archivos** subdivididos en:
  - `clientes/` - Gestión de clientes
  - `configuracion/` - Configuración de empresa
  - `dashboard/` - Dashboards principales
  - `documentos/` - Gestión de documentos (cotizaciones, órdenes)
  - `reportes/` - Reportes y estadísticas
  - `repuestos/` - Gestión de repuestos
  - `servicios/` - Catálogo de servicios
  - `vehiculos/` - Gestión de vehículos
  - `common/` - Componentes compartidos
  - `includes/` - Includes reutilizables
  - `layout/` - Layouts base
  - `pdf/` - Templates para PDF
  - `widgets/` - Widgets personalizados
  - `cl/es/` - Templates específicas de Chile en español
  - `us/` - Templates específicas de USA (en/es)

**Módulos de Aplicación Genéricos:**
- `app/` - Templates de módulos de aplicación
  - `clientes/`, `configuracion/`, `dashboard/`, `documentos/`, 
  - `otros_servicios/`, `reportes/`, `repuestos/`, `servicios/`,
  - `suscriptor/`, `tecnicos/`, `vehiculos/`

**Módulos por País:**
- `cl/` - Templates específicas de Chile (12 archivos)
- `us/` - Templates específicas de USA (13 archivos)

**Módulos de Funcionalidad:**
- `components/` - Componentes reutilizables (1 archivo)
- `common/` - Templates comunes (4 archivos)
- `demo/` - Demos (1 archivo)
- `emails/` - Templates de email (4 archivos)
- `notifications/` - Notificaciones (4 archivos)
- `errors/` - Páginas de error (1 archivo)
- `ia/` - Funcionalidades de IA (2 archivos)
- `landing/` - Landing pages (2 archivos)
- `onboarding/` - Onboarding de usuarios (1 archivo)
- `pdf/` - PDFs generales (3 archivos)
- `public/` - Páginas públicas (7 archivos)
- `repuestos/` - Dashboard de repuestos (1 archivo)
- `servicios/` - Menús de servicios (2 archivos)
- `settings/` - Configuración de empresa (1 archivo)
- `suscripcion/` - Suscripciones (1 archivo)
- `suspension/` - Suspensión de cuenta (3 archivos)

**Archivos raíz:**
- `base.html` - Template base principal
- `legal.html` - Página legal
- `selector_pais_egarage.html` - Selector de país

#### B. Carpeta de App: `/taller/templates/`
Contiene **19 archivos** organizados en:

- `components/`
  - `country_badge.html` - Badge de país
- `portal/`
  - `base.html` - Base del portal de clientes
  - `dashboard.html` - Dashboard del portal
- `suscripcion/`
  - `activar_codigo.html` - Activación de código
  - `prueba_ya_usada.html` - Mensaje de prueba usada
  - `registro.html` - Registro de suscripción
- `taller/`
  - `configuracion.html` - Configuración
  - `suscriptor_dashboard.html` - Dashboard del suscriptor
  - `common/`
    - `debug_i18n.html.py` - Debug de i18n (archivo .py, no .html)
  - `documentos/`
    - `enviar_email_form.html` - Form de envío de email
    - `opciones_entrega.html` - Opciones de entrega
    - `pdf_template.html` - Template de PDF
  - `emails/`
    - `documento_email.html` - Email de documento
    - `documento_email.txt` - Email texto plano
  - `reportes/`
    - `comparativo_precios.html` - Comparativo de precios
    - `dashboard_inteligencia_operativa.html` - Dashboard de BI
    - `dashboard_rentabilidad.html` - Dashboard de rentabilidad
    - `rentabilidad.html` - Reporte de rentabilidad
    - `servicios_subcontratados_backup.html` - Backup
    - `servicios_subcontratados.html` - Servicios subcontratados

#### C. Carpetas de Backup (PENDIENTES DE LIMPIEZA)
- `_backup_templates_20251026_215347/` - Backup completo de templates (275 archivos)
- `_backup_templates_20251026_215527/` - Backup de account, admin, etc. (múltiples archivos)
- `revision templates/` - Múltiples carpetas de revisión
  - `templates/` - 268 archivos
  - `templates_backup_20250917_183530/`
  - `templates_canonical/` - 439 archivos
  - `templates_legacy_quarantine/` - 1 archivo
  - `templates_short_backup_20250917_191011/` - 58 archivos

## 2. PROBLEMAS IDENTIFICADOS

### A. Duplicación de Templates
1. **Duplicación entre `/templates/taller/` y `/taller/templates/taller/`**
   - Ambas carpetas tienen subcarpetas de `taller/` con contenido similar
   - Puede causar confusión sobre qué template se está usando

2. **Templates de documentos duplicadas**
   - `/templates/taller/documentos/` tiene 25 archivos
   - `/taller/templates/taller/documentos/` tiene 3 archivos

3. **Templates de reportes duplicadas**
   - `/templates/taller/reportes/` tiene 15 archivos
   - `/taller/templates/taller/reportes/` tiene 6 archivos

### B. Organización Confusa
1. **Estructura app/ vs taller/**
   - `/templates/app/` y `/templates/taller/` tienen estructura similar
   - No está claro cuál es la diferencia entre ambas

2. **Localización inconsistente**
   - Algunas templates country-aware están en `/templates/cl/` y `/templates/us/`
   - Otras están en `/templates/taller/cl/` y `/templates/taller/us/`

3. **Backups en la carpeta principal**
   - Múltiples carpetas de backup ocupando espacio
   - Dificultan la navegación del proyecto

### C. Convenciones de Django
Según las mejores prácticas de Django:
- Templates de la app deberían estar en `app_name/templates/app_name/`
- Templates globales deberían estar en `/templates/`
- La configuración actual mezcla ambos enfoques

## 3. PLAN DE REORGANIZACIÓN

### Fase 1: Análisis y Respaldo ✅
- [x] Documentar estructura actual
- [x] Identificar duplicados
- [x] Crear este documento de planificación

### Fase 2: Consolidación de Templates de Taller
**Objetivo:** Mover todas las templates de `/taller/templates/taller/` a `/templates/taller/`

**Acción:**
1. Comparar archivos duplicados entre ambas ubicaciones
2. Mantener la versión más reciente/completa
3. Mover templates únicas de `/taller/templates/` a `/templates/taller/`
4. Actualizar referencias en código si es necesario

**Templates a mover:**
- `/taller/templates/taller/documentos/` → `/templates/taller/documentos/`
- `/taller/templates/taller/reportes/` → `/templates/taller/reportes/`
- `/taller/templates/taller/emails/` → `/templates/taller/emails/`

### Fase 3: Organización de Módulos de App
**Objetivo:** Consolidar `/templates/app/` en la estructura principal

**Decisión:**
- Si `app/` es una aplicación Django separada → mantener en su lugar
- Si es parte de `taller/` → mover a `/templates/taller/`
- Si son templates compartidas → mantener en `/templates/`

### Fase 4: Estandarización de Localización
**Objetivo:** Unificar estructura country-aware

**Estructura propuesta:**
```
/templates/
  ├── taller/
  │   ├── cl/
  │   │   └── es/
  │   │       ├── clientes/
  │   │       ├── documentos/
  │   │       ├── vehiculos/
  │   │       └── ...
  │   └── us/
  │       ├── en/
  │       │   ├── clientes/
  │       │   ├── documentos/
  │       │   └── ...
  │       └── es/
  │           └── ...
  ├── cl/
  │   └── es/
  │       └── (páginas públicas/landing)
  └── us/
      ├── en/
      └── es/
```

### Fase 5: Limpieza de Backups
**Objetivo:** Remover carpetas de backup de la carpeta principal

**Acción:**
1. Mover a carpeta `/backups/templates/` fuera del proyecto principal
2. Crear un único archivo comprimido con todos los backups
3. Eliminar carpetas de backup de la raíz

**Carpetas a limpiar:**
- `_backup_templates_20251026_215347/`
- `_backup_templates_20251026_215527/`
- `revision templates/`

### Fase 6: Consolidación de Templates Especiales
**Objetivo:** Organizar templates de funcionalidades especiales

**Portal de Clientes:**
- Mover `/taller/templates/portal/` → `/templates/portal/`
- Es una funcionalidad independiente que merece su propio módulo

**Components y Common:**
- Consolidar `/templates/components/` y `/templates/common/`
- Crear estructura clara de componentes reutilizables

**Suscripciones:**
- Consolidar templates de suscripción dispersas
- Unificar en `/templates/suscripcion/`

## 4. ESTRUCTURA FINAL PROPUESTA

```
/templates/
  ├── base.html                      # Base global
  ├── legal.html                     # Legal
  │
  ├── account/                       # Autenticación django-allauth
  ├── registration/                  # Password reset
  ├── auth/                          # Auth adicional
  │
  ├── admin/                         # Admin Django
  ├── admin_panel/                   # Panel admin custom
  │
  ├── analytics/                     # Analítica
  ├── business_intelligence/         # BI
  │
  ├── components/                    # Componentes reutilizables
  ├── common/                        # Templates comunes
  ├── includes/                      # Includes globales
  │
  ├── portal/                        # Portal de clientes
  │   ├── base.html
  │   ├── dashboard.html
  │   └── ...
  │
  ├── taller/                        # App principal taller
  │   ├── base.html
  │   ├── dashboard.html
  │   ├── clientes/
  │   ├── configuracion/
  │   ├── documentos/
  │   ├── reportes/
  │   ├── repuestos/
  │   ├── servicios/
  │   ├── vehiculos/
  │   ├── tecnicos/
  │   ├── common/
  │   ├── layout/
  │   ├── includes/
  │   ├── widgets/
  │   ├── pdf/
  │   ├── emails/
  │   │
  │   ├── cl/es/                     # Chile - Español
  │   │   ├── clientes/
  │   │   ├── documentos/
  │   │   ├── dashboard/
  │   │   └── ...
  │   │
  │   └── us/                        # USA
  │       ├── en/                    # Inglés
  │       │   ├── clientes/
  │       │   ├── documentos/
  │       │   └── ...
  │       └── es/                    # Español
  │           └── ...
  │
  ├── suscripcion/                   # Módulo de suscripciones
  │   ├── activar_codigo.html
  │   ├── registro.html
  │   ├── usuario_existente.html
  │   └── ...
  │
  ├── suspension/                    # Suspensión de cuenta
  ├── onboarding/                    # Onboarding
  │
  ├── emails/                        # Emails globales
  ├── notifications/                 # Notificaciones
  │
  ├── pdf/                           # PDFs globales
  │   ├── base_document.html
  │   ├── header.html
  │   └── footer.html
  │
  ├── errors/                        # Páginas de error
  │
  ├── ia/                            # Funcionalidades IA
  │
  ├── landing/                       # Landings globales
  ├── public/                        # Páginas públicas
  │   ├── cl/                        # Landing Chile
  │   └── us/                        # Landing USA
  │
  └── demo/                          # Demos

/taller/templates/
  └── (VACÍO - todo movido a /templates/taller/)

/backups/
  └── templates/                     # Backups históricos
      ├── backup_20251026_215347.zip
      ├── backup_20251026_215527.zip
      └── revision_templates.zip
```

## 5. BENEFICIOS DE LA REORGANIZACIÓN

### A. Claridad
- Estructura clara y predecible
- Fácil localizar cualquier template
- Separación clara entre templates globales y de app

### B. Mantenibilidad
- Elimina duplicación
- Facilita actualizaciones
- Reduce errores de usar template incorrecta

### C. Escalabilidad
- Fácil agregar nuevos países/idiomas
- Estructura preparada para nuevos módulos
- Patrón claro para templates country-aware

### D. Mejores Prácticas
- Sigue convenciones de Django
- Organización por funcionalidad
- Separación de concerns

## 6. PRÓXIMOS PASOS

1. ✅ Crear este documento de planificación
2. ⏳ Comparar y consolidar templates duplicadas
3. ⏳ Mover templates de `/taller/templates/` a `/templates/`
4. ⏳ Verificar que no se rompa ninguna referencia
5. ⏳ Limpiar carpetas de backup
6. ⏳ Crear documento final de estructura
7. ⏳ Ejecutar tests para verificar integridad

## 7. NOTAS IMPORTANTES

- **NO BORRAR** templates sin antes verificar que no están en uso
- **RESPALDAR** antes de hacer cambios masivos
- **VERIFICAR** referencias en código Python (views, forms, etc.)
- **PROBAR** después de cada fase de reorganización
- **DOCUMENTAR** cualquier cambio en referencias de templates

---

**Documento creado por:** AI Assistant  
**Fecha:** 27 de Octubre, 2025  
**Proyecto:** eGarage - Gestión de Talleres






