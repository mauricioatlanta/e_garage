# 🧠 Módulo de Inteligencia de Negocio - E-Garage

## 📋 Descripción General

El módulo de inteligencia de negocio proporciona análisis profundos y visualizaciones interactivas para ayudar a los talleres a tomar decisiones informadas basadas en datos.

## 🚀 Funcionalidades Implementadas

### 1. 📊 Ranking de Servicios Más Vendidos
- **Objetivo**: Identificar qué servicios son más populares y rentables
- **Métricas**: 
  - Cantidad vendida
  - Ingresos totales
  - Precio promedio
- **Visualización**: Gráfico de barras interactivo
- **Utilidad**: Permite enfocar esfuerzos en servicios más demandados

### 2. 💰 Utilidad Neta por Repuesto
- **Objetivo**: Analizar la rentabilidad de cada repuesto
- **Métricas**:
  - Utilidad bruta (Ingresos - Costos)
  - Margen de utilidad porcentual
  - Cantidad vendida
  - Ingresos totales
- **Visualización**: Gráfico de dona y tabla detallada
- **Utilidad**: Identificar repuestos más rentables y ajustar precios

### 3. 👨‍🔧 Dashboard por Mecánico/Vendedor
- **Objetivo**: Evaluar el rendimiento individual de cada mecánico
- **Métricas**:
  - Total de documentos procesados
  - Repuestos vendidos
  - Servicios realizados
  - Ingresos generados
  - Promedio por documento
- **Visualización**: Tabla comparativa con barras de progreso
- **Utilidad**: Identificar mecánicos top y áreas de mejora

## 🔧 Instalación y Configuración

### Paso 1: Verificar Instalación
El módulo se integra automáticamente con el sistema existente. Las URLs están configuradas en:
- `taller/business_intelligence_urls.py`
- Integradas en `taller/urls.py`

### Paso 2: Generar Datos de Prueba
```bash
python manage.py generar_datos_bi --documentos 50 --dias 90
```

Parámetros disponibles:
- `--empresa-id`: ID específico de empresa (opcional)
- `--documentos`: Número de documentos a generar (default: 50)
- `--dias`: Días hacia atrás para generar datos (default: 90)

### Paso 3: Acceder al Dashboard
1. Iniciar sesión en el sistema
2. Ir al Dashboard principal
3. Hacer clic en "🧠 Inteligencia de Negocio"

O acceder directamente a: `http://localhost:8000/taller/business-intelligence/dashboard/`

## 📱 Funcionalidades del Dashboard

### 🎛️ Filtros Interactivos
- **Rango de fechas**: Seleccionar período específico de análisis
- **Actualización en tiempo real**: Botón para refrescar datos
- **Exportación**: Preparado para exportar a Excel/PDF (en desarrollo)

### 📈 Métricas Principales
- **Total de documentos** en el período
- **Ingresos totales** generados
- **Servicios realizados** 
- **Promedio diario** de ingresos

### 🎨 Visualizaciones
- **Gráficos interactivos** con Chart.js
- **Tablas responsivas** con Bootstrap
- **Barras de progreso** para comparaciones
- **Indicadores de color** para utilidades positivas/negativas

### 📊 APIs REST
El módulo incluye APIs para integración con otras herramientas:

- `GET /taller/business-intelligence/api/servicios-ranking/`
- `GET /taller/business-intelligence/api/repuestos-utilidad/`  
- `GET /taller/business-intelligence/api/mecanicos-stats/`

Todas las APIs soportan filtros por fecha:
```
?fecha_inicio=2025-01-01&fecha_fin=2025-12-31
```

## 🛠️ Estructura Técnica

### Archivos Principales
```
taller/
├── views/business_intelligence.py          # Lógica de negocio
├── business_intelligence_urls.py           # URLs del módulo
├── management/commands/generar_datos_bi.py # Comando para datos de prueba
└── templates/business_intelligence/
    └── dashboard.html                      # Template principal
```

### Modelos Utilizados
- `Documento`: Documentos del taller (presupuestos, órdenes, facturas)
- `RepuestoDocumento`: Repuestos asociados a documentos
- `ServicioDocumento`: Servicios asociados a documentos
- `Repuesto`: Catálogo de repuestos
- `Mecanico`: Personal del taller
- `Empresa`: Datos multiempresa

### Cálculos Clave

#### Utilidad por Repuesto
```python
utilidad_bruta = ingresos_totales - (precio_compra * cantidad_vendida)
margen_utilidad = (utilidad_bruta / ingresos_totales) * 100
```

#### Performance por Mecánico
```python
promedio_por_documento = ingresos_totales / total_documentos
```

## 🎯 Casos de Uso

### Para Gerentes/Propietarios
- **Análisis de rentabilidad**: Identificar servicios y repuestos más rentables
- **Control de inventario**: Ver qué repuestos tienen mejor rotación
- **Evaluación de personal**: Comparar rendimiento entre mecánicos

### Para Jefes de Taller
- **Planificación de trabajo**: Enfocar en servicios más demandados
- **Gestión de stock**: Reordenar repuestos con mejor margen
- **Capacitación**: Identificar mecánicos que necesitan apoyo

### Para Vendedores
- **Estrategias de venta**: Promover servicios con mejor margen
- **Negociación**: Datos para justificar precios
- **Metas**: Objetivos basados en datos históricos

## 🔄 Funcionalidades Futuras

### En Desarrollo
- [ ] Exportación a Excel/PDF
- [ ] Alertas automáticas por bajo rendimiento
- [ ] Comparación con períodos anteriores
- [ ] Proyecciones basadas en tendencias
- [ ] Integración con sistema de inventario

### Mejoras Planificadas
- [ ] Dashboard móvil optimizado
- [ ] Notificaciones push
- [ ] Análisis predictivo con IA
- [ ] Benchmarking con otros talleres
- [ ] Reportes automatizados por email

## 📞 Soporte

Para problemas o sugerencias relacionadas con el módulo de inteligencia de negocio:

1. **Logs del sistema**: Revisar `logs/` para errores
2. **Datos de prueba**: Ejecutar comando de generación de datos
3. **Verificación**: Usar `diagnostico_usuarios.py` para validar configuración

## 🏆 Beneficios Clave

✅ **Decisiones basadas en datos** en lugar de intuición  
✅ **Identificación de oportunidades** de crecimiento  
✅ **Optimización de inventario** y recursos  
✅ **Mejora del rendimiento** del personal  
✅ **Incremento de rentabilidad** general del taller  

---

*Módulo desarrollado para E-Garage - Sistema de Gestión de Talleres*
