from django.http import HttpResponse
from django.urls import path


def ping(_):
    return HttpResponse("pong")


urlpatterns = [path("ping/", ping)]
