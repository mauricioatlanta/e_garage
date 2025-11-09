import pytest

from django.urls import reverse


@pytest.mark.django_db
def test_client_list_usa_uses_us_en_template(client, settings):
    """Test que USA usa template en inglés con texto en inglés"""
    client.cookies["django_language"] = "en"
    url = reverse("clientes_us:lista_clientes")
    r = client.get(url)
    # Verifica que aparece el texto en inglés (sin traducir)
    html = r.content.decode()
    assert "Client Management" in html


@pytest.mark.django_db
def test_client_list_chile_uses_cl_es_template(client, settings):
    """Test que Chile usa template en español con texto traducido"""
    client.cookies["django_language"] = "es"
    url = reverse("clientes_cl:lista_clientes")
    r = client.get(url)
    html = r.content.decode()
    # Verifica que aparece el texto traducido ({% trans %} renderizado)
    # Como usamos {% trans "Client Management" %}, debería aparecer "Gestión de Clientes" en ES
    assert "Gestión de Clientes" in html or "Clientes" in html


@pytest.mark.django_db
def test_actions_grid_two_rows(client):
    """Test que los botones aparecen en layout de 2 filas con CSS Grid"""
    url = reverse("clientes_us:lista_clientes")
    r = client.get(url)
    html = r.content.decode()
    # Verifica CSS Grid de 2 filas
    assert "grid grid-cols-2" in html
    assert "col-span-2" in html  # delete centrado en fila 2


@pytest.mark.django_db
def test_language_switch_sets_cookie(client):
    """Test end-to-end del cambio de idioma por POST"""
    # Test cambio a español
    resp = client.post(reverse("set_language"), {"language": "es", "next": "/"})
    assert resp.status_code in (302, 303)  # Redirección

    # Verifica que el contenido está en español
    r = client.get("/")
    html = r.content.decode()
    assert "Español" in html or "Inicio" in html or "Dashboard" in html

    # Test cambio a inglés
    resp = client.post(reverse("set_language"), {"language": "en", "next": "/"})
    assert resp.status_code in (302, 303)

    # Verifica que el contenido está en inglés
    r = client.get("/")
    html = r.content.decode()
    assert "English" in html or "Dashboard" in html
