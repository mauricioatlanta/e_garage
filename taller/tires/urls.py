from django.urls import path
from . import views
from . import views_reportes
app_name = "tires"
urlpatterns = [
    path("reportes/", views_reportes.reportes_vulcanizacion, name="reportes_vulcanizacion"),
    path("", views.lista_tires, name="lista_tires"),
    path("crear/", views.crear_tire, name="crear_tire"),
    path("editar/<int:pk>/", views.editar_tire, name="editar_tire"),
    path("<int:pk>/eliminar/", views.eliminar_tire, name="eliminar_tire"),
    path("buscar/", views.buscar_tires, name="buscar_tires"),
    path("autocomplete/", views.autocomplete_tires, name="autocomplete_tires"),
    # Interno (solo tú, con login)
    path("kiosko/", views.kiosko_tires, name="kiosko_tires"),
    # Públicos (sin login, lo que ve todo el mundo)
    path("public/", views.kiosko_publico, name="kiosko_publico"),
    path("public/<slug:slug>/", views.kiosko_mi_taller_publico, name="kiosko_publico_slug"),
    path("public/<int:slug>/", views.kiosko_mi_taller_publico, name="kiosko_publico_id"),
    path("todos/", views.kiosko_global_publico, name="kiosko_global"),
]
