# taller/pdf/urls.py
from django.urls import path

from . import views

app_name = "pdf"

urlpatterns = [
    path("header/<int:pk>/", views.header, name="header"),
    path("footer/<int:pk>/", views.footer, name="footer"),
]
