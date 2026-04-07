import pytest
from django.urls import reverse


@pytest.mark.parametrize(
    ("view_name", "expected_path"),
    [
        ("chile:root", "/cl/es/"),
        ("chile:chile_home", "/cl/es/"),
        ("uruguay:root", "/uy/"),
        ("uruguay:uruguay_home", "/uy/"),
        ("uruguay_es:root", "/uy/es/"),
        ("uruguay_es:uruguay_home", "/uy/es/"),
        ("argentina:root", "/ar/"),
        ("argentina:argentina_home", "/ar/"),
        ("argentina_es:root", "/ar/es/"),
        ("argentina_es:argentina_home", "/ar/es/"),
        ("peru:root", "/pe/es/"),
        ("peru:peru_home", "/pe/es/"),
        ("colombia:root", "/co/es/"),
        ("colombia:colombia_home", "/co/es/"),
        ("ecuador:root", "/ec/es/"),
        ("ecuador:ecuador_home", "/ec/es/"),
        ("venezuela:root", "/ve/es/"),
        ("venezuela:venezuela_home", "/ve/es/"),
        ("mexico:root", "/mx/es/"),
        ("mexico:mexico_home", "/mx/es/"),
        ("brasil:root", "/br/"),
        ("brasil:brasil_home", "/br/"),
    ],
)
def test_country_namespaces_expose_root_alias_and_legacy_name(view_name, expected_path):
    assert reverse(view_name) == expected_path
