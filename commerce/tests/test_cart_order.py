"""
Tests de Cart + Order (carrito anónimo y ciclo de pedido).

Cobertura:
1.  CartService.add_item crea ítem con cantidad correcta.
2.  add_item acumula si el producto ya estaba.
3.  update_item cambia la cantidad.
4.  update_item con 0 elimina el ítem.
5.  remove_item elimina el ítem.
6.  CartService.total calcula bien.
7.  item_count suma unidades.
8.  Dos carritos distintos (empresas distintas) no comparten ítems.
9.  OrderService.create_from_cart congela SKU, nombre y precio.
10. create_from_cart vacía el carrito.
11. create_from_cart en carrito vacío lanza ValueError.
12. CommerceOrderItem.subtotal = unit_price × quantity.
13. GET /commerce/carrito/ devuelve 200.
14. POST /commerce/carrito/agregar/ añade ítem y redirige.
15. POST /commerce/carrito/actualizar/ con cantidad=0 elimina ítem.
16. POST /commerce/carrito/eliminar/ elimina ítem.
17. GET /commerce/checkout/ con carrito vacío redirige al carrito.
18. POST /commerce/checkout/ válido crea pedido y redirige.
19. GET /commerce/pedido/<num>/ del tenant correcto devuelve 200.
20. GET /commerce/pedido/<num>/ de otro tenant devuelve 404.
"""
import pytest
from decimal import Decimal
from django.test import Client, override_settings

from commerce.models import CommerceProduct
from commerce.models.cart import CommerceCart, CommerceCartItem
from commerce.models.order import CommerceOrder, CommerceOrderItem
from commerce.services.cart_service import CartService
from commerce.services.order_service import OrderService
from commerce.tests.conftest import make_category, make_product


# ── Helpers ───────────────────────────────────────────────────────────────────

SESSION_A = "a" * 32
SESSION_B = "b" * 32


def make_cart(empresa, session_key=SESSION_A):
    return CartService.get_or_create(empresa, session_key)


# ── 1. add_item crea ítem ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_add_item_creates(empresa):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    cart = make_cart(empresa)
    item = CartService.add_item(cart, p, 2)
    assert item.quantity == 2
    assert CommerceCartItem.objects.filter(cart=cart, product=p).count() == 1


# ── 2. add_item acumula ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_add_item_accumulates(empresa):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    cart = make_cart(empresa)
    CartService.add_item(cart, p, 1)
    CartService.add_item(cart, p, 3)
    item = CommerceCartItem.objects.get(cart=cart, product=p)
    assert item.quantity == 4


# ── 3. update_item cambia cantidad ────────────────────────────────────────────

@pytest.mark.django_db
def test_update_item_changes_quantity(empresa):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    cart = make_cart(empresa)
    CartService.add_item(cart, p, 2)
    CartService.update_item(cart, p, 5)
    assert CommerceCartItem.objects.get(cart=cart, product=p).quantity == 5


# ── 4. update_item con 0 elimina ─────────────────────────────────────────────

@pytest.mark.django_db
def test_update_item_zero_removes(empresa):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    cart = make_cart(empresa)
    CartService.add_item(cart, p, 1)
    CartService.update_item(cart, p, 0)
    assert not CommerceCartItem.objects.filter(cart=cart, product=p).exists()


# ── 5. remove_item ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_remove_item(empresa):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    cart = make_cart(empresa)
    CartService.add_item(cart, p, 1)
    CartService.remove_item(cart, p)
    assert not CommerceCartItem.objects.filter(cart=cart).exists()


# ── 6. total ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_cart_total(empresa):
    cat = make_category(empresa)
    from taller.tests.factories import RepuestoFactory
    r1 = RepuestoFactory(empresa=empresa, precio_venta=Decimal("1000"))
    r2 = RepuestoFactory(empresa=empresa, precio_venta=Decimal("500"))
    p1 = make_product(empresa, repuesto=r1, category=cat)
    p2 = make_product(empresa, repuesto=r2, category=cat)
    cart = make_cart(empresa)
    CartService.add_item(cart, p1, 2)  # 2000
    CartService.add_item(cart, p2, 3)  # 1500
    assert CartService.total(cart) == Decimal("3500")


# ── 7. item_count ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_item_count(empresa):
    cat = make_category(empresa)
    p1 = make_product(empresa, category=cat)
    p2 = make_product(empresa, category=cat)
    cart = make_cart(empresa)
    CartService.add_item(cart, p1, 2)
    CartService.add_item(cart, p2, 3)
    assert CartService.item_count(cart) == 5


# ── 8. Aislamiento multi-tenant ───────────────────────────────────────────────

@pytest.mark.django_db
def test_carts_are_tenant_isolated(empresa, empresa_b):
    cat_a = make_category(empresa)
    cat_b = make_category(empresa_b)
    p_a = make_product(empresa, category=cat_a)
    p_b = make_product(empresa_b, category=cat_b)
    cart_a = make_cart(empresa, SESSION_A)
    cart_b = make_cart(empresa_b, SESSION_A)
    CartService.add_item(cart_a, p_a, 1)
    CartService.add_item(cart_b, p_b, 1)
    assert CartService.item_count(cart_a) == 1
    assert CartService.item_count(cart_b) == 1
    assert not CommerceCartItem.objects.filter(cart=cart_a, product=p_b).exists()
    assert not CommerceCartItem.objects.filter(cart=cart_b, product=p_a).exists()


# ── 9. create_from_cart congela datos ────────────────────────────────────────

@pytest.mark.django_db
def test_order_freezes_sku_name_price(empresa):
    cat = make_category(empresa)
    from taller.tests.factories import RepuestoFactory
    r = RepuestoFactory(empresa=empresa, nombre="Filtro de aceite", part_number="F-001",
                        precio_venta=Decimal("4990"))
    p = make_product(empresa, repuesto=r, category=cat)
    cart = make_cart(empresa)
    CartService.add_item(cart, p, 2)

    order = OrderService.create_from_cart(cart, {
        "name": "Juan Pérez",
        "email": "juan@test.cl",
    })

    item = order.items.get()
    assert item.sku == "F-001"
    assert item.name == "Filtro de aceite"
    assert item.unit_price == Decimal("4990")
    assert item.quantity == 2
    assert item.subtotal == Decimal("9980")


# ── 10. create_from_cart vacía el carrito ────────────────────────────────────

@pytest.mark.django_db
def test_order_clears_cart(empresa):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    cart = make_cart(empresa)
    CartService.add_item(cart, p, 1)
    OrderService.create_from_cart(cart, {"name": "A", "email": "a@b.cl"})
    assert CartService.item_count(cart) == 0


# ── 11. Carrito vacío lanza ValueError ───────────────────────────────────────

@pytest.mark.django_db
def test_order_empty_cart_raises(empresa):
    cart = make_cart(empresa)
    with pytest.raises(ValueError, match="vacío"):
        OrderService.create_from_cart(cart, {"name": "A", "email": "a@b.cl"})


# ── 12. CommerceOrderItem.subtotal ────────────────────────────────────────────

def test_order_item_subtotal():
    item = CommerceOrderItem(unit_price=Decimal("100"), quantity=3)
    assert item.subtotal == Decimal("300")


# ── Helpers de vista ─────────────────────────────────────────────────────────

def commerce_client(empresa, session_key=SESSION_A):
    client = Client(HTTP_HOST="teststore.local")
    session = client.session
    session["_session_key_override"] = session_key
    session.save()
    return client


def _client(empresa):
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        return Client(HTTP_HOST="teststore.local")


# ── 13. GET /carrito/ devuelve 200 ────────────────────────────────────────────

@pytest.mark.django_db
def test_cart_detail_200(empresa):
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = Client(HTTP_HOST="teststore.local").get("/commerce/carrito/")
    assert resp.status_code == 200


# ── 14. POST /carrito/agregar/ ───────────────────────────────────────────────

@pytest.mark.django_db
def test_cart_add_view(empresa):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        client = Client(HTTP_HOST="teststore.local")
        resp = client.post("/commerce/carrito/agregar/", {"slug": p.slug, "quantity": 2})
    assert resp.status_code == 302
    assert resp["Location"] == "/commerce/carrito/"
    # Verificar que el carrito tiene el ítem
    session_key = client.session.session_key
    cart = CommerceCart.objects.get(empresa=empresa, session_key=session_key)
    assert CartService.item_count(cart) == 2


# ── 15. POST /carrito/actualizar/ con 0 elimina ──────────────────────────────

@pytest.mark.django_db
def test_cart_update_zero_removes(empresa):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        client = Client(HTTP_HOST="teststore.local")
        # Primero añadir
        client.post("/commerce/carrito/agregar/", {"slug": p.slug, "quantity": 1})
        # Luego actualizar a 0
        resp = client.post("/commerce/carrito/actualizar/", {"slug": p.slug, "quantity": 0})
    assert resp.status_code == 302
    session_key = client.session.session_key
    cart = CommerceCart.objects.get(empresa=empresa, session_key=session_key)
    assert CartService.item_count(cart) == 0


# ── 16. POST /carrito/eliminar/ ──────────────────────────────────────────────

@pytest.mark.django_db
def test_cart_remove_view(empresa):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        client = Client(HTTP_HOST="teststore.local")
        client.post("/commerce/carrito/agregar/", {"slug": p.slug, "quantity": 1})
        resp = client.post("/commerce/carrito/eliminar/", {"slug": p.slug})
    assert resp.status_code == 302
    session_key = client.session.session_key
    cart = CommerceCart.objects.get(empresa=empresa, session_key=session_key)
    assert CartService.item_count(cart) == 0


# ── 17. GET /checkout/ con carrito vacío redirige ────────────────────────────

@pytest.mark.django_db
def test_checkout_empty_cart_redirects(empresa):
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        resp = Client(HTTP_HOST="teststore.local").get("/commerce/checkout/")
    # Sin sesión → sin carrito → redirige
    assert resp.status_code in (302, 301)


# ── 18. POST /checkout/ válido crea pedido ───────────────────────────────────

@pytest.mark.django_db
def test_checkout_post_creates_order(empresa):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        client = Client(HTTP_HOST="teststore.local")
        client.post("/commerce/carrito/agregar/", {"slug": p.slug, "quantity": 1})
        resp = client.post("/commerce/checkout/", {
            "name": "María García",
            "email": "maria@test.cl",
            "phone": "+56912345678",
            "shipping_address": "Av. Providencia 123, Santiago",
            "notes": "",
        })
    assert resp.status_code == 302
    assert CommerceOrder.objects.filter(empresa=empresa, customer_email="maria@test.cl").exists()
    order = CommerceOrder.objects.get(empresa=empresa, customer_email="maria@test.cl")
    assert resp["Location"] == f"/commerce/pedido/{order.order_number}/"


# ── 19. GET /pedido/<num>/ del tenant correcto ───────────────────────────────

@pytest.mark.django_db
def test_order_received_page(empresa):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        client = Client(HTTP_HOST="teststore.local")
        client.post("/commerce/carrito/agregar/", {"slug": p.slug, "quantity": 1})
        client.post("/commerce/checkout/", {
            "name": "Test", "email": "t@t.cl", "phone": "", "shipping_address": "", "notes": ""
        })
        order = CommerceOrder.objects.get(empresa=empresa)
        resp = client.get(f"/commerce/pedido/{order.order_number}/")
    assert resp.status_code == 200
    assert order.order_number.encode() in resp.content


# ── 20. GET /pedido/<num>/ de otro tenant devuelve 404 ───────────────────────

@pytest.mark.django_db
def test_order_received_wrong_tenant(empresa, empresa_b):
    cat = make_category(empresa)
    p = make_product(empresa, category=cat)
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa.pk}):
        client = Client(HTTP_HOST="teststore.local")
        client.post("/commerce/carrito/agregar/", {"slug": p.slug, "quantity": 1})
        client.post("/commerce/checkout/", {
            "name": "Test", "email": "t@t.cl", "phone": "", "shipping_address": "", "notes": ""
        })
        order = CommerceOrder.objects.get(empresa=empresa)

    # Intentar acceder desde tenant B
    with override_settings(COMMERCE_TENANT_MAP={"teststore.local": empresa_b.pk}):
        resp = Client(HTTP_HOST="teststore.local").get(f"/commerce/pedido/{order.order_number}/")
    assert resp.status_code == 404
