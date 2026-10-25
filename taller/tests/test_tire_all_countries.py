from taller.config.rubros import RUBROS_TALLER
from taller.config.rubros_translations import get_rubros_choices_for_country


def test_tire_is_available_for_every_supported_country():
    supported = ("US", "CL", "MX", "PE", "VE", "BR", "CO", "AR", "EC", "UY")
    codes = {code for code, _label in RUBROS_TALLER}
    assert "TIRE" in codes

    for country in supported:
        choices = dict(get_rubros_choices_for_country(country))
        assert "TIRE" in choices, country
        assert choices["TIRE"] != "TIRE", country
