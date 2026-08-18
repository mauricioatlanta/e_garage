from django.urls import path

from commerce.views import cart, catalog, checkout, pages, payment, sitemap as sitemap_views
from commerce.views.admin import categories as admin_cat
from commerce.views.admin import dashboard as admin_dash
from commerce.views.admin import media as admin_media
from commerce.views.admin import products as admin_prod

app_name = "commerce"

urlpatterns = [
    # ── Commerce Admin (ERP autenticado) ─────────────────────────────────────
    path("admin/", admin_dash.commerce_admin_dashboard, name="admin_dashboard"),
    path("admin/categories/", admin_cat.category_list, name="admin_category_list"),
    path("admin/categories/nueva/", admin_cat.category_create, name="admin_category_create"),
    path("admin/categories/<int:pk>/editar/", admin_cat.category_edit, name="admin_category_edit"),
    path("admin/categories/<int:pk>/toggle/", admin_cat.category_toggle_active, name="admin_category_toggle"),
    path("admin/categories/<int:pk>/eliminar/", admin_cat.category_delete, name="admin_category_delete"),
    path("admin/products/", admin_prod.product_list, name="admin_product_list"),
    path("admin/products/<int:pk>/editar/", admin_prod.product_edit, name="admin_product_edit"),
    path("admin/products/<int:pk>/toggle/", admin_prod.product_toggle_publishable, name="admin_product_toggle"),
    path("admin/products/bulk/", admin_prod.product_bulk_action, name="admin_product_bulk"),
    path("admin/media/", admin_media.media_library, name="admin_media_library"),
    path("admin/products/<int:pk>/images/<int:image_pk>/eliminar/", admin_prod.product_image_delete, name="admin_product_image_delete"),
    path("admin/products/<int:pk>/images/<int:image_pk>/primary/", admin_prod.product_image_set_primary, name="admin_product_image_primary"),

    # Catálogo
    path("", catalog.catalog_home, name="home"),
    path("categoria/<slug:slug>/", catalog.category_detail, name="category"),
    path("p/<slug:slug>/", catalog.product_detail, name="product"),
    path("buscar/", catalog.search_view, name="search"),
    path("page/<slug:slug>/", pages.static_page_detail, name="page"),
    path("buscar-vehiculo/", catalog.vehicle_search_view, name="vehicle_search"),
    # API interna
    path("api/vehicle-models/", catalog.api_vehicle_models, name="api_vehicle_models"),
    # Carrito
    path("carrito/", cart.cart_detail, name="cart"),
    path("carrito/agregar/", cart.cart_add, name="cart_add"),
    path("carrito/actualizar/", cart.cart_update, name="cart_update"),
    path("carrito/eliminar/", cart.cart_remove, name="cart_remove"),
    # Checkout
    path("checkout/", checkout.checkout_view, name="checkout"),
    path("pedido/<str:order_number>/", checkout.order_received, name="order_received"),
    # Pagos
    path("pedido/<str:order_number>/pago/", payment.payment_select, name="payment_select"),
    path("pedido/<str:order_number>/pago/iniciar/", payment.payment_start, name="payment_start"),
    path("pago/retorno/", payment.payment_return, name="payment_return"),
    path("pedido/<str:order_number>/pago/cancelado/", payment.payment_cancel, name="payment_cancel"),
    # SEO
    path("sitemap.xml", sitemap_views.commerce_sitemap_xml, name="sitemap"),
]
