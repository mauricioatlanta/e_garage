from django.urls import path

from . import views

app_name = "qa_control"

urlpatterns = [
    path("", views.control, name="control"),
    path("exit/", views.exit_control, name="exit"),
]
