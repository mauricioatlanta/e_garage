from django.urls import path

from . import views_staff

app_name = "reciclaje_staff"

urlpatterns = [
    path("", views_staff.dashboard, name="dashboard"),
    path(
        "api/catalitico-por-codigo/",
        views_staff.api_catalitico_por_codigo,
        name="api_catalitico_por_codigo",
    ),
    path(
        "api/producto-chatarra/",
        views_staff.api_producto_chatarra,
        name="api_producto_chatarra",
    ),
    path("compras/nueva/", views_staff.crear_compra, name="crear_compra"),
    path("compras/", views_staff.listado_compras, name="listado_compras"),
    path("compras/<int:pk>/", views_staff.detalle_compra, name="detalle_compra"),
    path("compras/<int:pk>/editar/", views_staff.editar_compra, name="editar_compra"),
    path("compras/<int:pk>/eliminar/", views_staff.eliminar_compra, name="eliminar_compra"),
    path("ventas/nueva/", views_staff.crear_venta, name="crear_venta"),
    path("ventas/", views_staff.listado_ventas, name="listado_ventas"),
    path("ventas/<int:pk>/", views_staff.detalle_venta, name="detalle_venta"),
    path("stock/", views_staff.resumen_stock, name="resumen_stock"),
    path("stock/categorias/nueva/", views_staff.crear_categoria_chatarra, name="crear_categoria_chatarra"),
    path("stock/productos/nuevo/", views_staff.crear_producto_chatarra, name="crear_producto_chatarra"),
    path(
        "catalitico/<int:pk>/editar/",
        views_staff.editar_catalitico,
        name="editar_catalitico",
    ),
    path(
        "catalitico/<int:pk>/eliminar/",
        views_staff.eliminar_catalitico,
        name="eliminar_catalitico",
    ),
    path("reportes/", views_staff.reporte_fechas, name="reporte_fechas"),
]
