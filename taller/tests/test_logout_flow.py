import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_account_logout_clears_session_without_sessioninterrupted(client):
    user = get_user_model().objects.create_user(
        username="logout-user",
        email="logout@example.com",
        password="Secret12345!",
    )
    client.force_login(user)

    session = client.session
    session["country"] = "cl"
    session["django_language"] = "es"
    session["account_login"] = {"initiated_at": 0}
    session.save()

    response = client.post(reverse("account_logout"), follow=False)

    assert response.status_code == 302
    assert "_auth_user_id" not in client.session
