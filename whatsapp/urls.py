"""
URLs para eGarage Air - WhatsApp v2 Final
"""
from django.urls import path
from . import views

app_name = 'whatsapp'

urlpatterns = [
    path('webhook/', views.webhook, name='webhook'),
]
