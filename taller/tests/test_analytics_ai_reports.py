import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from taller.analytics.ai_reports import AIReportEngine
from taller.models.empresa import Empresa


@pytest.mark.django_db
def test_dashboard_distribution_handles_empty_company():
    user = get_user_model().objects.create_user(
        username="analytics_empty_company",
        email="analytics-empty@example.com",
        password="pass",
    )
    empresa = Empresa.objects.create(user=user, nombre_taller="Analytics Empty", pais="CL")

    engine = AIReportEngine(empresa)

    assert engine._get_vehicle_distribution() == []
    assert engine._get_clientes_distribution() == []


@pytest.mark.django_db
def test_dashboard_data_handles_empty_company():
    user = get_user_model().objects.create_user(
        username="analytics_dashboard_empty",
        email="analytics-dashboard-empty@example.com",
        password="pass",
    )
    empresa = Empresa.objects.create(user=user, nombre_taller="Analytics Dashboard", pais="CL")

    data = AIReportEngine(empresa).get_dashboard_data()

    assert data["charts"]["vehicle_distribution"] == []
    assert data["operations"]["vehiculos_activos"] == 0
    assert data["operations"]["clientes_activos"] == 0


@pytest.mark.django_db
def test_dashboard_view_renders_for_empty_company():
    user = get_user_model().objects.create_user(
        username="analytics_dashboard_view",
        email="analytics-dashboard-view@example.com",
        password="pass",
    )
    Empresa.objects.create(
        user=user,
        nombre_taller="Analytics View",
        pais="CL",
        onboarding_completado=True,
    )
    client = Client()
    client.force_login(user)

    response = client.get("/analytics/dashboard/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_real_time_metrics_api_handles_empty_company():
    user = get_user_model().objects.create_user(
        username="analytics_realtime_empty",
        email="analytics-realtime-empty@example.com",
        password="pass",
    )
    Empresa.objects.create(
        user=user,
        nombre_taller="Analytics Realtime",
        pais="CL",
        onboarding_completado=True,
    )
    client = Client()
    client.force_login(user)

    response = client.get("/analytics/real-time/")

    assert response.status_code == 200
    assert response.json()["today_documents"] == 0
