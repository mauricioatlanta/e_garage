from django.urls import path
from django.http import HttpResponse

app_name = "ops"


def home(request):
    return HttpResponse("ops ok")


urlpatterns = [
    path("", home, name="home"),
]
