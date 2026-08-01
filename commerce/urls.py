from django.urls import path

from commerce.views import cart, catalog, checkout, pages, payment

app_name = "commerce"

urlpatterns = [
    # Catálogo
    path("", catalog.catalog_home, name="home"),
    path("categoria/<slug:slug>/", catalog.category_detail, name="category"),
    path("p/<slug:slug>/", catalog.product_detail, name="product"),
    path("buscar/", catalog.search_view, name="search"),
    path("page/<slug:slug>/", pages.static_page_detail, name="page"),
    # Carrito
    path("carrito/", cart.cart_detail, name="cart"),
    path("carrito/agregar/", cart.cart_add, name="cart_add"),
    path("carrito/actualizar/", cart.cart_update, name="cart_update"),
    path("carrito/eliminar/", cart.cart_remove, name="cart_remove"),
    # Checkout
    path("checkout/", checkout.checkout_view, name="checkout"),
    path("pedido/<str:order_number>/", checkout.order_received, name="order_received"),
    # Pagos
    path("pedido/<str:order_number>/pago/iniciar/", payment.payment_start, name="payment_start"),
    path("pago/retorno/", payment.payment_return, name="payment_return"),
    path("pedido/<str:order_number>/pago/cancelado/", payment.payment_cancel, name="payment_cancel"),
]
