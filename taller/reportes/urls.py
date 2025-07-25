from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.reportes_dashboard, name='reportes_dashboard'),
    path('dashboard/', views.reportes_dashboard, name='dashboard'),
    path('repuestos/', views.reporte_repuestos, name='reporte_repuestos'),
    path('servicios/', views.reporte_servicios, name='reporte_servicios'),
    path('inteligencia/', views.dashboard_inteligencia_operativa, name='inteligencia_operativa'),
    path('diagnostico/', views.diagnostico_ia, name='diagnostico_ia'),
    
    # === REPORTES AVANZADOS DE RENTABILIDAD ===
    # Estas rutas las voy a importar dinámicamente para evitar imports circulares
    
    # === NUEVAS RUTAS PARA REPORTES POR MECÁNICO ===
    path('mecanicos/', views.reportes_mecanicos, name='reportes_mecanicos'),
    path('mecanicos/excel/', views.exportar_mecanicos_excel, name='exportar_mecanicos_excel'),
    path('mecanicos/pdf/<int:mecanico_id>/', views.generar_pdf_mecanico, name='generar_pdf_mecanico'),
    path('mecanicos/whatsapp/<int:mecanico_id>/', views.generar_resumen_whatsapp_mecanico, name='generar_resumen_whatsapp_mecanico'),
    path('api/mecanicos/chart-data/', views.api_mecanicos_chart_data, name='api_mecanicos_chart_data'),
    
    # === NUEVAS RUTAS PARA REPORTES POR FECHA ===
    path('por-fecha/', views.reportes_por_fecha, name='reportes_por_fecha'),
    path('repuestos-fecha/<str:desde>/<str:hasta>/', views.reportes_repuestos_fecha, name='reportes_repuestos_fecha'),
    path('servicios-fecha/<str:desde>/<str:hasta>/', views.reportes_servicios_fecha, name='reportes_servicios_fecha'),
    path('otros-fecha/<str:desde>/<str:hasta>/', views.reportes_otros_servicios_fecha, name='reportes_otros_servicios_fecha'),
]

# Agregar rutas de rentabilidad dinámicamente para evitar imports circulares
try:
    from .reportes_avanzados import dashboard_rentabilidad, reportes_rentabilidad, reporte_comparativo_precios, reporte_servicios_subcontratados
    
    urlpatterns += [
        path('dashboard-rentabilidad/', dashboard_rentabilidad, name='dashboard_rentabilidad'),
        path('rentabilidad/', reportes_rentabilidad, name='reportes_rentabilidad'),
        path('comparativo-precios/', reporte_comparativo_precios, name='reporte_comparativo_precios'),
        path('servicios-subcontratados/', reporte_servicios_subcontratados, name='reporte_servicios_subcontratados'),
    ]
except ImportError:
    # Si hay problemas de importación, continuar sin estas rutas
    pass