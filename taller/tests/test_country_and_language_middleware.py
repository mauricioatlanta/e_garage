import pytest


@pytest.mark.django_db
def test_root_redirects_once_to_canonical_country_and_language(client, settings):
    settings.SECURE_SSL_REDIRECT = False

    response = client.get("/", follow=True)

    assert response.status_code == 200
    assert len(response.redirect_chain) == 1

    redirect_url, status_code = response.redirect_chain[0]
    assert status_code in (301, 302)
    assert redirect_url == "/cl/es/"
