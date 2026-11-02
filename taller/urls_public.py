from django.urls import path

from taller.views_extra.storefront import kiosko_centralizado, tienda_storefront, tienda_storefront_slug

urlpatterns = [
    path("kiosko/", kiosko_centralizado, name="kiosko_centralizado"),
    path("empresa/<int:empresa_id>/", tienda_storefront, name="tienda_storefront"),
    path("<slug:slug>/", tienda_storefront_slug, name="tienda_storefront_slug"),
]
