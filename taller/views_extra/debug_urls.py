from django.urls import path

from . import debug_branding

urlpatterns = [
    path('', debug_branding.debug_branding, name='debug_branding'),
]
