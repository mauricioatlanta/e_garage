from django.urls import path

from taller.views_extra.storefront import kiosko_centralizado, tienda_storefront

urlpatterns = [
    path("kiosko/", kiosko_centralizado, name="kiosko_centralizado"),
    path("<slug:slug>/", tienda_storefront, name="tienda_storefront"),
]
