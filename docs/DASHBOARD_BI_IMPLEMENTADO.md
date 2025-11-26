# 📊 Dashboard de Inteligencia de Negocios (BI) - Implementación Completa

## 📋 Resumen

Implementación completa del Dashboard de BI con agregaciones multi-tenant eficientes usando el ORM de Django. Todas las consultas se ejecutan en la base de datos para evitar loops en Python.

**Features:**
- ✅ KPIs principales del mes actual
- ✅ Gráfico de ventas anuales (12 meses) con Chart.js
- ✅ Ranking de técnicos más productivos
- ✅ Agregaciones eficientes en DB (no loops en Python)
- ✅ Caching automático para optimización
- ✅ Multi-tenant seguro

## 🎯 Problema Resuelto

**Desafío Técnico:**
- ❌ Agregaciones lentas con loops en Python
- ❌ Sin cache (recarga datos cada vez)
- ❌ Sin dashboard centralizado de BI

**Solución:**
- ✅ Agregaciones en DB usando ORM (annotate, aggregate, TruncMonth)
- ✅ Caching automático (1 hora por defecto)
- ✅ Servicio dedicado reutilizable

## 📁 Archivos Creados

### 1. Servicio de Dashboard
**Archivo**: `taller/services/dashboard_service.py`

Servicio dedicado que maneja agregaciones eficientes:

```python
class DashboardService:
    def get_kpis_principales(self, force_refresh=False):
        """Retorna KPIs principales del mes"""
    
    def get_ventas_anuales_chart(self, meses=12, force_refresh=False):
        """Retorna datos para gráfico de líneas"""
    
    def get_ranking_tecnicos(self, top=5, force_refresh=False):
        """Retorna ranking de técnicos más productivos"""
```

### 2. Vista del Dashboard
**Archivo**: `taller/views/dashboard_bi.py`

Vista basada en clases (TemplateView):

```python
class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "taller/dashboard/home.html"
```

### 3. Template HTML
**Archivo**: `templates/taller/dashboard/home.html`

Template con:
- Tarjetas de KPIs (Ventas, OTs, Facturas, Ticket Promedio)
- Gráfico de ventas con Chart.js
- Ranking de técnicos
- Diseño responsive con Tailwind CSS

### 4. URLs Agregadas
**Archivo**: `taller/urls.py`

URL agregada:
- `/taller/dashboard/bi/` - Dashboard de BI

## 🔧 Configuración

### 1. Servicio Disponible

Ya está exportado en `taller/services/__init__.py`:

```python
from taller.services import DashboardService
```

### 2. Cache

El servicio usa Django cache automáticamente. Asegúrate de tener cache configurado:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        # o 'django.core.cache.backends.redis.RedisCache'
    }
}
```

## 🎨 Uso

### Desde el Servicio

```python
from taller.services import DashboardService

# Inicializar servicio
empresa = request.user.empresa
service = DashboardService(empresa, cache_enabled=True, cache_timeout=3600)

# Obtener KPIs
kpis = service.get_kpis_principales()
# Retorna: {
#     'total_ventas': Decimal('50000.00'),
#     'total_ot': 10,
#     'total_facturas': 5,
#     'total_presupuestos': 8,
#     'ticket_promedio': Decimal('3333.33'),
#     'tasa_conversion': 62.5,
# }

# Obtener gráfico
chart_data = service.get_ventas_anuales_chart(meses=12)
# Retorna: {
#     'labels': ['Ene 2024', 'Feb 2024', ...],
#     'data': [50000.0, 75000.0, ...],
# }

# Obtener ranking
tecnicos = service.get_ranking_tecnicos(top=5)
# Retorna: QuerySet de técnicos con:
# - total_trabajos: int
# - total_generado: Decimal
```

### Desde el Template

```html
<!-- Ver dashboard -->
<a href="{% url 'taller:dashboard_bi' %}" class="btn btn-primary">
    📊 Dashboard BI
</a>

<!-- Refrescar datos (forzar actualización) -->
<a href="{% url 'taller:dashboard_bi' %}?refresh=true" class="btn btn-secondary">
    🔄 Actualizar
</a>
```

## 📊 Características

### 1. Agregaciones Eficientes

**Antes (Lento):**
```python
# ❌ Loop en Python (lento con muchos documentos)
docs = Documento.objects.filter(empresa=empresa)
total = 0
for doc in docs:
    total += doc.total
```

**Ahora (Rápido):**
```python
# ✅ Agregación en DB (rápido)
stats = Documento.objects.filter(empresa=empresa).aggregate(
    total_ventas=Sum('total'),
    total_ot=Count('id', filter=Q(tipo='OT')),
)
```

### 2. Caching Automático

El servicio cachea resultados automáticamente:

```python
# Cache habilitado (default: 1 hora)
service = DashboardService(empresa, cache_enabled=True, cache_timeout=3600)

# Forzar refresco
kpis = service.get_kpis_principales(force_refresh=True)

# Invalidar cache manualmente
service.invalidate_cache()
```

### 3. Multi-Tenant Seguro

Todas las consultas filtran por empresa:

```python
# ✅ Siempre filtrar por empresa
Documento.objects.filter(
    empresa=self.empresa,  # 🔒 Multi-tenant
    estado='EMITIDO'
)
```

### 4. Agregaciones con Filtros

Usa `filter` en `Count` y `Sum` para agregaciones condicionales:

```python
# Contar solo OTs
total_ot = Count('id', filter=Q(tipo='OT'))

# Sumar solo documentos emitidos
total_ventas = Sum('total', filter=Q(estado='EMITIDO'))
```

## 📈 KPIs Implementados

### Tarjetas Principales

1. **Ventas este Mes**
   - Total de ventas del mes actual
   - Solo documentos emitidos

2. **Órdenes Realizadas**
   - Total de OTs del mes
   - Solo documentos emitidos

3. **Facturas Emitidas**
   - Total de facturas del mes
   - Solo documentos emitidos

4. **Ticket Promedio**
   - Promedio de ventas por documento
   - Calculado en DB: `Sum('total') / Count('id')`

### KPIs Adicionales

5. **Presupuestos**
   - Total de presupuestos del mes

6. **Tasa de Conversión**
   - Porcentaje de presupuestos convertidos a facturas
   - Fórmula: `(facturas / presupuestos_anteriores) * 100`

## 🎨 Gráfico de Ventas

El gráfico muestra la tendencia de ventas de los últimos 12 meses:

- **Tipo**: Línea (line chart)
- **Librería**: Chart.js
- **Datos**: Agrupados por mes usando `TruncMonth`
- **Formato**: "Ene 2024", "Feb 2024", etc.

## 🏆 Ranking de Técnicos

Muestra los top técnicos más productivos del mes:

- **Métrica 1**: Total de trabajos (documentos realizados)
- **Métrica 2**: Total generado (suma de totales)
- **Orden**: Por total generado descendente
- **Top**: 5 técnicos por defecto

## ⚡ Optimización

### 1. Cache

- **Tiempo de cache**: 1 hora por defecto
- **Clave de cache**: `dashboard_{empresa_id}_{tipo}`
- **Invalidación**: Automática después de timeout o manual con `invalidate_cache()`

### 2. Agregaciones en DB

- **Sin loops en Python**: Todo se hace en la base de datos
- **Índices**: Asegúrate de tener índices en `empresa`, `fecha_emision`, `estado`, `tipo`

### 3. Queries Optimizadas

```python
# ✅ Prefetch relacionadas
documento.lineas_repuesto.select_related('repuesto').all()

# ✅ Usar values() para agrupar
.values('mes').annotate(total=Sum('total'))

# ✅ Filtrar antes de agregar
.filter(empresa=self.empresa, estado='EMITIDO')
```

## 🚀 Próximos Pasos Opcionales

1. **Filtros de Fecha**
   - Selector de rango de fechas en el frontend
   - "Semana pasada", "Mes pasado", "Último año"

2. **Exportar a PDF/Excel**
   - Exportar dashboard completo

3. **Métricas Avanzadas**
   - Margen de ganancia
   - Costos vs. Ingresos
   - Proyecciones con ML

4. **Alertas Inteligentes**
   - Notificaciones cuando KPIs bajan
   - Comparación con períodos anteriores

## ✅ Checklist de Implementación

- [x] Servicio DashboardService creado
- [x] Vista DashboardHomeView creada
- [x] Template HTML con Chart.js creado
- [x] URLs agregadas
- [x] Agregaciones eficientes en DB
- [x] Caching implementado
- [x] Multi-tenant seguro
- [x] Logging de operaciones
- [ ] Configurar cache en producción
- [ ] Probar con datos reales
- [ ] Optimizar índices en DB

## 🎉 Resultado

Con este dashboard, tu sistema ahora:
- ✅ Muestra KPIs principales en tiempo real
- ✅ Visualiza tendencias de ventas con gráficos
- ✅ Identifica técnicos más productivos
- ✅ Es rápido (agregaciones en DB + cache)
- ✅ Es seguro (multi-tenant)

**¡Dashboard de BI completo y optimizado!** 🎊

