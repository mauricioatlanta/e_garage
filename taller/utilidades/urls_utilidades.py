# urls/utilidades_urls.py – Rutas para AJAX y exportaciones

from django.urls import path
from taller.views.utilidades import (
    repuesto_info,
    exportar_excel_repuestos
)

urlpatterns = [
    path('ajax/repuesto-info/', repuesto_info, name='repuesto_info'),
    path('exportar/repuestos/excel/', exportar_excel_repuestos, name='exportar_excel_repuestos'),
]
