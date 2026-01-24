# 📊 Guía de Uso: Reportes y Análisis de Kilometraje

## 📋 Resumen

Este documento explica cómo usar las funcionalidades de reportes y análisis basadas en `KilometrajeRegistro` para generar inteligencia operativa valiosa para el taller.

---

## 🎯 Funcionalidades Disponibles

### 1. Trazabilidad de Garantías
### 2. Frecuencia de Visita y Desgaste
### 3. Recordatorios de Mantenimiento Predictivo
### 4. Historial de Mantenimiento Detallado

---

## 🔧 Uso Básico

### Inicializar el Reporte

```python
from taller.models import Empresa
from taller.reportes.kilometraje_reportes import ReporteKilometraje

# Obtener la empresa del usuario
empresa = request.user.empresa

# Crear instancia del reporte
reporte = ReporteKilometraje(empresa)
```

---

## 1️⃣ Trazabilidad de Garantías

### Verificar si un Documento de Garantía está Dentro del Límite

```python
from taller.models import Documento

# Obtener documentos
documento_original = Documento.objects.get(pk=123)  # Reparación original
documento_garantia = Documento.objects.get(pk=456)   # Ingreso por garantía

# Verificar garantía
resultado = reporte.verificar_garantia(documento_garantia, documento_original)

# Resultado:
# {
#     'dentro_garantia': True/False,
#     'kilometros_recorridos': 3500,
#     'limite_garantia_km': 5000,
#     'porcentaje_uso': 70.0,
#     'kilometraje_original': 50000,
#     'kilometraje_garantia': 53500,
#     'mensaje': 'Kilómetros recorridos: 3,500 km. Límite de garantía: 5,000 km. Uso: 70.0%'
# }

if resultado['dentro_garantia']:
    print("✅ La garantía aplica")
else:
    print("❌ La garantía no aplica - se excedió el límite de kilometraje")
```

### Ejemplo en Vista Django

```python
from django.shortcuts import render, get_object_or_404
from taller.models import Documento
from taller.reportes.kilometraje_reportes import ReporteKilometraje

def verificar_garantia_view(request, doc_garantia_id, doc_original_id):
    empresa = request.user.empresa
    reporte = ReporteKilometraje(empresa)
    
    doc_garantia = get_object_or_404(Documento, pk=doc_garantia_id, empresa=empresa)
    doc_original = get_object_or_404(Documento, pk=doc_original_id, empresa=empresa)
    
    resultado = reporte.verificar_garantia(doc_garantia, doc_original)
    
    return render(request, 'reportes/verificar_garantia.html', {
        'resultado': resultado,
        'documento_garantia': doc_garantia,
        'documento_original': doc_original
    })
```

---

## 2️⃣ Frecuencia de Visita y Desgaste

### Reporte de Frecuencia de Visitas

```python
# Generar reporte completo
reporte_frecuencia = reporte.reporte_frecuencia_visitas()

# Estructura del resultado:
# {
#     'vehiculos': [
#         {
#             'vehiculo': <Vehiculo>,
#             'patente': 'ABC123',
#             'cliente': 'Juan Pérez',
#             'total_visitas': 5,
#             'km_promedio_entre_servicios': 8500.0,
#             'dias_promedio_entre_servicios': 120.5,
#             'km_total_recorridos': 45000,
#             'fecha_ultima_visita': datetime(...)
#         },
#         ...
#     ],
#     'estadisticas_generales': {
#         'total_vehiculos': 25,
#         'total_visitas': 150,
#         'km_total_promedio': 42000.0
#     }
# }

# Mostrar top 5 vehículos con más visitas
for vehiculo_data in reporte_frecuencia['vehiculos'][:5]:
    print(f"{vehiculo_data['patente']}: {vehiculo_data['total_visitas']} visitas")
```

### Reporte de Rentabilidad por Kilómetro

```python
# Generar reporte de rentabilidad
reporte_rentabilidad = reporte.reporte_rentabilidad_por_kilometro()

# Estructura:
# {
#     'vehiculos': [
#         {
#             'vehiculo': <Vehiculo>,
#             'patente': 'ABC123',
#             'cliente': 'Juan Pérez',
#             'total_ventas': Decimal('150000.00'),
#             'km_total': 45000,
#             'rentabilidad_por_km': 3.33,  # $3.33 por km
#             'total_visitas': 5
#         },
#         ...
#     ],
#     'ranking_rentabilidad': [...]  # Top 10
# }

# Mostrar top 3 más rentables
for vehiculo_data in reporte_rentabilidad['ranking_rentabilidad'][:3]:
    print(f"{vehiculo_data['patente']}: ${vehiculo_data['rentabilidad_por_km']}/km")
```

### Ejemplo en Vista Django

```python
from django.shortcuts import render
from taller.reportes.kilometraje_reportes import ReporteKilometraje

def reporte_frecuencia_view(request):
    empresa = request.user.empresa
    reporte = ReporteKilometraje(empresa)
    
    datos = reporte.reporte_frecuencia_visitas()
    
    return render(request, 'reportes/frecuencia_visitas.html', {
        'vehiculos': datos['vehiculos'],
        'estadisticas': datos['estadisticas_generales']
    })
```

---

## 3️⃣ Recordatorios de Mantenimiento Predictivo

### Generar Lista de Recordatorios

```python
# Recordatorios para cambio de aceite (cada 10,000 km)
# Alertar cuando falten 1,000 km o menos
recordatorios = reporte.recordatorios_mantenimiento(
    servicio_km=10000,      # Servicio cada 10,000 km
    margen_alerta=1000     # Alertar cuando falten 1,000 km
)

# Estructura:
# [
#     {
#         'vehiculo': <Vehiculo>,
#         'patente': 'ABC123',
#         'cliente': 'Juan Pérez',
#         'telefono_cliente': '+56912345678',
#         'email_cliente': 'juan@example.com',
#         'km_actual': 19000,
#         'km_ultimo_servicio': 10000,
#         'km_proximo_servicio': 20000,
#         'km_faltantes': 1000,
#         'fecha_ultimo_servicio': datetime(...),
#         'urgencia': 'alta'  # o 'media'
#     },
#     ...
# ]

# Enviar recordatorios por WhatsApp/Email
for recordatorio in recordatorios:
    if recordatorio['urgencia'] == 'alta':
        # Enviar mensaje urgente
        mensaje = (
            f"⚠️ {recordatorio['cliente']}, tu vehículo {recordatorio['patente']} "
            f"está a {recordatorio['km_faltantes']} km de necesitar mantenimiento. "
            f"¡Agenda tu servicio ahora!"
        )
        # enviar_whatsapp(recordatorio['telefono_cliente'], mensaje)
```

### Ejemplo de Vista con Recordatorios

```python
from django.shortcuts import render
from taller.reportes.kilometraje_reportes import ReporteKilometraje

def recordatorios_mantenimiento_view(request):
    empresa = request.user.empresa
    reporte = ReporteKilometraje(empresa)
    
    # Recordatorios para diferentes servicios
    cambio_aceite = reporte.recordatorios_mantenimiento(
        servicio_km=10000,
        margen_alerta=1000
    )
    
    revision_mayor = reporte.recordatorios_mantenimiento(
        servicio_km=50000,
        margen_alerta=5000
    )
    
    return render(request, 'reportes/recordatorios.html', {
        'cambio_aceite': cambio_aceite,
        'revision_mayor': revision_mayor
    })
```

---

## 4️⃣ Historial de Mantenimiento Detallado

### Generar Historial Completo de un Vehículo

```python
from taller.models import Vehiculo

# Obtener vehículo
vehiculo = Vehiculo.objects.get(pk=1, empresa=empresa)

# Generar historial
historial = reporte.historial_mantenimiento_vehiculo(vehiculo)

# Estructura:
# {
#     'vehiculo': <Vehiculo>,
#     'historial': [
#         {
#             'documento': <Documento>,
#             'numero_documento': 'OT-001',
#             'tipo': 'Orden de Trabajo',
#             'fecha': date(2024, 1, 15),
#             'kilometraje': 50000,
#             'trabajos_realizados': 'Cambio de aceite, Filtro de aire, Revisión general',
#             'monto': Decimal('45000.00'),
#             'tecnico': 'Carlos Méndez',
#             'estado': 'EMITIDO'
#         },
#         ...
#     ],
#     'resumen': {
#         'total_servicios': 5,
#         'total_gastado': Decimal('150000.00'),
#         'km_promedio_entre_servicios': 8500.0,
#         'dias_promedio_entre_servicios': 120.5,
#         'fecha_primer_servicio': date(2023, 6, 10),
#         'fecha_ultimo_servicio': date(2024, 1, 15)
#     }
# }

# Mostrar historial
for entrada in historial['historial']:
    print(f"{entrada['fecha']} - {entrada['kilometraje']} km - {entrada['monto']}")
```

### Exportar Historial para Portal del Cliente

```python
# Exportar en formato estructurado
exportacion = reporte.exportar_historial_vehiculo(vehiculo, formato='dict')

# Esta estructura puede ser:
# - Convertida a JSON para API
# - Exportada a PDF
# - Mostrada en Portal del Cliente
# - Enviada por email al cliente

import json
json_data = json.dumps(exportacion, default=str, indent=2)
```

### Ejemplo de Vista para Historial

```python
from django.shortcuts import render, get_object_or_404
from taller.models import Vehiculo
from taller.reportes.kilometraje_reportes import ReporteKilometraje

def historial_vehiculo_view(request, vehiculo_id):
    empresa = request.user.empresa
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id, empresa=empresa)
    
    reporte = ReporteKilometraje(empresa)
    historial = reporte.historial_mantenimiento_vehiculo(vehiculo)
    
    return render(request, 'reportes/historial_vehiculo.html', {
        'historial_data': historial
    })
```

---

## 🔍 Métodos Helper en los Modelos

### Métodos en Vehiculo

```python
from taller.models import Vehiculo, Documento

vehiculo = Vehiculo.objects.get(pk=1)

# Obtener kilometraje actual
km_actual = vehiculo.kilometraje_actual

# Calcular kilómetros recorridos desde un documento
documento_original = Documento.objects.get(pk=123)
resultado = vehiculo.kilometros_recorridos_desde_documento(documento_original)
# {
#     'kilometros_recorridos': 3500,
#     'kilometraje_original': 50000,
#     'kilometraje_actual': 53500,
#     'dias_transcurridos': 90
# }

# Obtener estadísticas de uso
stats = vehiculo.estadisticas_uso()
# {
#     'total_registros': 5,
#     'km_promedio_entre_servicios': 8500.0,
#     'dias_promedio_entre_servicios': 120.5,
#     'km_total_recorridos': 45000,
#     'fecha_primer_registro': datetime(...),
#     'fecha_ultimo_registro': datetime(...)
# }
```

### Métodos en KilometrajeRegistro

```python
from taller.models import KilometrajeRegistro

registro = KilometrajeRegistro.objects.get(pk=1)

# Obtener registro anterior
registro_anterior = KilometrajeRegistro.obtener_registro_anterior(
    vehiculo=registro.vehiculo,
    fecha_registro=registro.fecha_registro
)

# Calcular kilómetros recorridos desde otro registro
if registro_anterior:
    km_recorridos = registro.kilometros_recorridos_desde(registro_anterior)
    dias = registro.dias_desde_registro_anterior()
```

---

## 📊 Ejemplos de Integración en Vistas

### Dashboard con Recordatorios

```python
from django.shortcuts import render
from taller.reportes.kilometraje_reportes import ReporteKilometraje

def dashboard_view(request):
    empresa = request.user.empresa
    reporte = ReporteKilometraje(empresa)
    
    # Obtener recordatorios urgentes
    recordatorios = reporte.recordatorios_mantenimiento(
        servicio_km=10000,
        margen_alerta=1000
    )
    
    # Filtrar solo los urgentes
    recordatorios_urgentes = [
        r for r in recordatorios 
        if r['urgencia'] == 'alta'
    ]
    
    return render(request, 'dashboard.html', {
        'recordatorios_urgentes': recordatorios_urgentes[:5]  # Top 5
    })
```

### API Endpoint para Historial

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from taller.models import Vehiculo
from taller.reportes.kilometraje_reportes import ReporteKilometraje

@require_http_methods(["GET"])
def api_historial_vehiculo(request, vehiculo_id):
    empresa = request.user.empresa
    
    try:
        vehiculo = Vehiculo.objects.get(pk=vehiculo_id, empresa=empresa)
        reporte = ReporteKilometraje(empresa)
        historial = reporte.exportar_historial_vehiculo(vehiculo)
        
        return JsonResponse(historial, safe=False)
    except Vehiculo.DoesNotExist:
        return JsonResponse({'error': 'Vehículo no encontrado'}, status=404)
```

---

## 🎯 Casos de Uso Reales

### 1. Verificar Garantía al Ingresar un Vehículo

```python
# Cuando un cliente trae su vehículo por garantía
def procesar_garantia(request, doc_garantia_id, doc_original_id):
    empresa = request.user.empresa
    reporte = ReporteKilometraje(empresa)
    
    doc_garantia = Documento.objects.get(pk=doc_garantia_id)
    doc_original = Documento.objects.get(pk=doc_original_id)
    
    verificacion = reporte.verificar_garantia(doc_garantia, doc_original)
    
    if verificacion['dentro_garantia']:
        # Aplicar garantía
        return render(request, 'garantia_aplicada.html', {
            'verificacion': verificacion
        })
    else:
        # Rechazar garantía
        return render(request, 'garantia_rechazada.html', {
            'verificacion': verificacion,
            'razon': 'Excedido límite de kilometraje'
        })
```

### 2. Enviar Recordatorios Automáticos

```python
# Tarea programada (Celery, cron, etc.)
def enviar_recordatorios_diarios():
    from taller.models import Empresa
    
    empresas = Empresa.objects.filter(suscripcion_activa=True)
    
    for empresa in empresas:
        reporte = ReporteKilometraje(empresa)
        recordatorios = reporte.recordatorios_mantenimiento(
            servicio_km=10000,
            margen_alerta=1000
        )
        
        for recordatorio in recordatorios:
            if recordatorio['urgencia'] == 'alta':
                # Enviar WhatsApp/Email
                enviar_notificacion(recordatorio)
```

### 3. Reporte Mensual de Rentabilidad

```python
def reporte_mensual_rentabilidad(request):
    empresa = request.user.empresa
    reporte = ReporteKilometraje(empresa)
    
    rentabilidad = reporte.reporte_rentabilidad_por_kilometro()
    
    # Generar gráficos y estadísticas
    return render(request, 'reportes/mensual_rentabilidad.html', {
        'rentabilidad': rentabilidad,
        'mes': timezone.now().strftime('%B %Y')
    })
```

---

## 📝 Notas Importantes

1. **Rendimiento**: Los reportes usan `prefetch_related` y `select_related` para optimizar consultas. Para grandes volúmenes de datos, considera agregar paginación.

2. **Configuración**: Los límites de garantía (5000 km) y servicios (10000 km) son valores por defecto. Considera hacerlos configurables desde `ConfiguracionEmpresa`.

3. **Validaciones**: Los métodos validan que existan registros de kilometraje. Si no hay datos, retornan valores `None` o estructuras vacías.

4. **Multi-tenant**: Todos los reportes filtran automáticamente por `empresa` para mantener el aislamiento de datos.

---

## 🚀 Próximos Pasos

1. **Crear vistas Django** para cada tipo de reporte
2. **Agregar templates** para visualizar los reportes
3. **Integrar con sistema de notificaciones** (WhatsApp/Email)
4. **Exportar a PDF/Excel** para historiales
5. **Crear API endpoints** para Portal del Cliente
6. **Agregar gráficos** usando Chart.js o similar

---

## 📚 Referencias

- Modelo `KilometrajeRegistro`: `taller/models/kilometraje.py`
- Modelo `Vehiculo`: `taller/models/vehiculos.py`
- Módulo de Reportes: `taller/reportes/kilometraje_reportes.py`

