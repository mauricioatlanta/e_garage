import glob

import pytest

from taller.config.country_settings import CountrySettings
from taller.forms.custom_signup import CustomSignupForm
from taller.models.empresa import Empresa
from taller.tests.factories import EmpresaFactory


class TestPaisChoicesParidad:
    def test_pais_choices_matches_country_settings_keys(self):
        pais_codes = {code for code, _ in Empresa.PAIS_CHOICES}
        assert pais_codes == set(CountrySettings.COUNTRIES.keys())

    def test_signup_country_choices_matches_country_settings_keys(self):
        signup_codes = {code for code, _ in CustomSignupForm.COUNTRY_CHOICES if code}
        assert signup_codes == set(CountrySettings.COUNTRIES.keys())

    def test_pais_choices_and_signup_are_identical_set(self):
        pais_codes = {code for code, _ in Empresa.PAIS_CHOICES}
        signup_codes = {code for code, _ in CustomSignupForm.COUNTRY_CHOICES if code}
        assert pais_codes == signup_codes

    def test_url_extra_country_files_are_subset_of_canonical(self):
        namespace_to_code = {
            cfg["namespace"]: code for code, cfg in CountrySettings.COUNTRIES.items()
        }
        excluded_stems = {"__init__", "portal_urls", "publico_urls", "admin_monitoring"}
        country_files = glob.glob("taller/urls_extra/*.py")
        for filepath in country_files:
            stem = filepath.split("/")[-1].replace(".py", "")
            if stem in excluded_stems or ".bak" in filepath:
                continue
            assert stem in namespace_to_code, (
                f"taller/urls_extra/{stem}.py has no matching country in CountrySettings.COUNTRIES"
            )


class TestCanonicalCompleteness:
    def test_every_country_has_currency(self):
        for code, cfg in CountrySettings.COUNTRIES.items():
            assert cfg.get("currency"), f"{code} is missing 'currency'"

    def test_every_country_has_timezone(self):
        for code, cfg in CountrySettings.COUNTRIES.items():
            assert cfg.get("timezone"), f"{code} is missing 'timezone'"


@pytest.mark.django_db
class TestEmpresaSaveAutoCorrection:
    def test_ar_empresa_gets_ars_on_save(self):
        e = EmpresaFactory(pais="AR", moneda="CLP")
        e.refresh_from_db()
        assert e.moneda == "ARS"

    def test_pe_empresa_gets_pen_on_save(self):
        e = EmpresaFactory(pais="PE", moneda="CLP")
        e.refresh_from_db()
        assert e.moneda == "PEN"

    def test_manually_set_moneda_not_overwritten(self):
        e = EmpresaFactory(pais="AR", moneda="USD")
        e.refresh_from_db()
        assert e.moneda == "USD"

    def test_ar_empresa_gets_buenos_aires_tz_when_utc(self):
        e = EmpresaFactory(pais="AR", zona_horaria="UTC")
        e.refresh_from_db()
        assert e.zona_horaria == "America/Argentina/Buenos_Aires"

    def test_cl_moneda_correction_unchanged(self):
        e = EmpresaFactory(pais="CL", moneda="USD")
        e.refresh_from_db()
        assert e.moneda == "CLP"
