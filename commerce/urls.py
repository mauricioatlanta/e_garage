from django.urls import path

from commerce.views import catalog, pages

app_name = "commerce"

urlpatterns = [
    path("", catalog.catalog_home, name="home"),
    path("categoria/<slug:slug>/", catalog.category_detail, name="category"),
    path("p/<slug:slug>/", catalog.product_detail, name="product"),
    path("buscar/", catalog.search_view, name="search"),
    path("page/<slug:slug>/", pages.static_page_detail, name="page"),
]
