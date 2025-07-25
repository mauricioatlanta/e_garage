"""
URLs para el sistema de emails de eGarage
"""

from django.urls import path
from taller.views.email_views import test_email_view, verificar_smtp_api

app_name = 'emails'

urlpatterns = [
    # Vista de prueba de emails
    path('test/', test_email_view, name='test_email'),
    
    # API para verificar SMTP
    path('verificar-smtp/', verificar_smtp_api, name='verificar_smtp'),
]
