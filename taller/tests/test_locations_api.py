# -*- coding: utf-8 -*-
"""
Tests para API de Ubicaciones

Verifica:
- Endpoint /api/locations funciona
- Retorna estados por país
- Retorna ciudades por estado
- Maneja errores correctamente
"""
import pytest
from django.test import Client
from django.urls import reverse

from taller.models import Estado, Ciudad


@pytest.mark.django_db
class TestLocationsAPI:
    """Tests para API de ubicaciones (/api/locations)"""

    def test_locations_requires_country(self, client):
        """Test: country es requerido"""
        url = "/api/locations/"
        response = client.get(url)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_locations_states_chile(self, client):
        """Test: obtener estados de Chile"""
        # Crear estado de prueba
        Estado.objects.create(
            nombre="Región Metropolitana", codigo="RM", pais="CL", sales_tax=19.00
        )

        url = "/api/locations/"
        response = client.get(url, {"country": "CL"})

        assert response.status_code == 200
        data = response.json()
        assert "states" in data
        assert len(data["states"]) >= 1

        # Verificar estructura
        state = data["states"][0]
        assert "id" in state
        assert "name" in state
        assert "code" in state

    def test_locations_states_peru(self, client):
        """Test: obtener departamentos de Perú"""
        # Crear departamento de prueba
        Estado.objects.create(nombre="Lima", codigo="LIM", pais="PE", sales_tax=18.00)

        url = "/api/locations/"
        response = client.get(url, {"country": "PE"})

        assert response.status_code == 200
        data = response.json()
        assert "states" in data

        # Verificar que hay al menos un departamento
        assert len(data["states"]) >= 1

    def test_locations_states_usa(self, client):
        """Test: obtener estados de USA"""
        # Crear estado de prueba
        Estado.objects.create(nombre="California", codigo="CA", pais="US", sales_tax=7.25)

        url = "/api/locations/"
        response = client.get(url, {"country": "US"})

        assert response.status_code == 200
        data = response.json()
        assert "states" in data
        assert len(data["states"]) >= 1

    def test_locations_cities_by_state(self, client):
        """Test: obtener ciudades por estado"""
        # Crear estado y ciudad
        estado = Estado.objects.create(nombre="Lima", codigo="LIM", pais="PE", sales_tax=18.00)

        Ciudad.objects.create(nombre="Lima", estado=estado, sales_tax_local=0.00)

        url = "/api/locations/"
        response = client.get(url, {"country": "PE", "state": "LIM"})

        assert response.status_code == 200
        data = response.json()
        assert "cities" in data
        assert len(data["cities"]) >= 1

        # Verificar estructura
        city = data["cities"][0]
        assert "id" in city
        assert "name" in city

    def test_locations_cities_empty_when_state_not_found(self, client):
        """Test: retorna array vacío si estado no existe"""
        url = "/api/locations/"
        response = client.get(url, {"country": "PE", "state": "NOEXISTE"})

        assert response.status_code == 200
        data = response.json()
        assert "cities" in data
        assert len(data["cities"]) == 0

    def test_locations_country_case_insensitive(self, client):
        """Test: country acepta mayúsculas y minúsculas"""
        # Crear estado
        Estado.objects.create(nombre="Lima", codigo="LIM", pais="PE", sales_tax=18.00)

        url = "/api/locations/"

        # Probar con minúsculas
        response1 = client.get(url, {"country": "pe"})
        assert response1.status_code == 200

        # Probar con mayúsculas
        response2 = client.get(url, {"country": "PE"})
        assert response2.status_code == 200

        # Ambos deben retornar lo mismo
        assert len(response1.json()["states"]) == len(response2.json()["states"])


@pytest.mark.django_db
class TestLocationsAPIMultipleCountries:
    """Tests para múltiples países"""

    def test_all_countries_return_states(self, client):
        """Test: todos los países soportados retornan estados"""
        countries = ["CL", "US", "BR", "PE", "VE"]

        # Crear al menos un estado por país
        for country in countries:
            Estado.objects.create(
                nombre=f"Estado {country}", codigo=f"{country}1", pais=country, sales_tax=10.00
            )

        url = "/api/locations/"

        for country in countries:
            response = client.get(url, {"country": country})
            assert response.status_code == 200, f"Failed for {country}"
            data = response.json()
            assert "states" in data, f"No states key for {country}"
            assert len(data["states"]) >= 1, f"No states for {country}"


# Fixture para crear datos de prueba
@pytest.fixture
def sample_location_data(db):
    """Fixture: crear datos de ubicación para testing"""
    # Perú
    lima = Estado.objects.create(nombre="Lima", codigo="LIM", pais="PE", sales_tax=18.00)
    Ciudad.objects.create(nombre="Lima", estado=lima)
    Ciudad.objects.create(nombre="Callao", estado=lima)

    # Chile
    rm = Estado.objects.create(
        nombre="Región Metropolitana", codigo="RM", pais="CL", sales_tax=19.00
    )
    Ciudad.objects.create(nombre="Santiago", estado=rm)

    # USA
    ca = Estado.objects.create(nombre="California", codigo="CA", pais="US", sales_tax=7.25)
    Ciudad.objects.create(nombre="Los Angeles", estado=ca)

    return {
        "peru": {"estado": lima, "ciudades": 2},
        "chile": {"estado": rm, "ciudades": 1},
        "usa": {"estado": ca, "ciudades": 1},
    }


@pytest.mark.django_db
def test_locations_with_sample_data(client, sample_location_data):
    """Test: API con datos de muestra completos"""
    url = "/api/locations/"

    # Test Perú
    response = client.get(url, {"country": "PE"})
    assert response.status_code == 200
    assert len(response.json()["states"]) >= 1

    # Test ciudades de Lima
    response = client.get(url, {"country": "PE", "state": "LIM"})
    assert response.status_code == 200
    assert len(response.json()["cities"]) == 2  # Lima y Callao
