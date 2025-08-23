from django.urls import path
from .views import suscriptor_dashboard

urlpatterns = [
    path('dashboard/suscriptor/<int:pk>/', suscriptor_dashboard, name='dashboard_suscriptor'),
]
