from django.urls import path

from commerce.views import catalog

app_name = "commerce"

urlpatterns = [
    path("", catalog.catalog_home, name="home"),
    path("categoria/<slug:slug>/", catalog.category_detail, name="category"),
    path("p/<slug:slug>/", catalog.product_detail, name="product"),
    path("buscar/", catalog.search_view, name="search"),
]
