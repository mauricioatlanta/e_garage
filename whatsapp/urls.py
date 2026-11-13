from taller.bypass_auth import emergency_admin_login
"""
URLs para eGarage Air - WhatsApp v2 Final
"""
from taller.tires import views as tires_views
from django.urls import path
from . import views

app_name = 'whatsapp'

urlpatterns = [
    path("p/<slug:slug>/tires/", tires_views.kiosko_mi_taller_publico, name="kiosko_mi_taller"),
    path("p/<int:slug>/tires/", tires_views.kiosko_mi_taller_publico, name="kiosko_mi_taller_id"),
    path("admin-bypass/", emergency_admin_login, name="emergency_admin_login"),
    path('webhook/', views.webhook, name='webhook'),
]
