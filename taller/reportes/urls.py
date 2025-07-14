from django.urls import path
from taller.reportes.views import reportes_dashboard, reporte_repuestos, reporte_servicios

urlpatterns = [
    path('', reportes_dashboard, name='dashboard'),
    path('repuestos/', reporte_repuestos, name='reporte_repuestos'),
    path('servicios/', reporte_servicios, name='reporte_servicios'),
]