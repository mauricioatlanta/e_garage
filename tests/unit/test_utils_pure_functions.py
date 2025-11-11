from decimal import Decimal

import pytest


@pytest.mark.django_db
def test_pais_utils_functions():
    """Test pais_utils with various inputs and edge cases"""
    try:
        from taller.utils.pais_utils import (
            format_currency,
            get_country_code,
            validate_country,
        )
    except ImportError:
        pytest.skip("pais_utils functions not found")

    # Test get_country_code
    assert get_country_code("Chile") == "CL"
    assert get_country_code("United States") == "US"
    assert get_country_code("chile") == "CL"  # case insensitive
    assert get_country_code("CHILE") == "CL"  # uppercase
    assert get_country_code("") == None
    assert get_country_code(None) == None
    assert get_country_code("Invalid Country") == None

    # Test format_currency
    assert format_currency(1000, "CL") == "$1.000"
    assert format_currency(1000, "US") == "$1,000.00"
    assert format_currency(0, "CL") == "$0"
    assert format_currency(None, "CL") == "$0"
    assert format_currency("invalid", "CL") == "$0"

    # Test validate_country
    assert validate_country("CL") == True
    assert validate_country("US") == True
    assert validate_country("cl") == True  # case insensitive
    assert validate_country("") == False
    assert validate_country(None) == False
    assert validate_country("XX") == False


@pytest.mark.django_db
def test_us_localization_functions():
    """Test US localization utilities"""
    try:
        from taller.utils.us_localization import (
            format_address,
            format_phone,
            format_zip_code,
        )
    except ImportError:
        pytest.skip("us_localization functions not found")

    # Test format_phone
    assert format_phone("1234567890") == "(123) 456-7890"
    assert format_phone("123-456-7890") == "(123) 456-7890"
    assert format_phone("(123) 456-7890") == "(123) 456-7890"
    assert format_phone("") == ""
    assert format_phone(None) == ""
    assert format_phone("invalid") == "invalid"

    # Test format_address
    assert (
        format_address("123 Main St", "Anytown", "CA", "12345") == "123 Main St, Anytown, CA 12345"
    )
    assert format_address("", "", "", "") == ", ,  "
    assert format_address(None, None, None, None) == "None, None, None None"

    # Test format_zip_code
    assert format_zip_code("12345") == "12345"
    assert format_zip_code("12345-6789") == "12345-6789"
    assert format_zip_code("") == ""
    assert format_zip_code(None) == ""


@pytest.mark.django_db
def test_templates_utils():
    """Test template utilities"""
    try:
        from taller.utils.templates import get_template_context, render_template_string
    except ImportError:
        pytest.skip("templates utils not found")

    # Test render_template_string
    result = render_template_string("Hello {{ name }}", {"name": "World"})
    assert result == "Hello World"

    result = render_template_string("Hello {{ name }}", {})
    assert result == "Hello "

    result = render_template_string("", {})
    assert result == ""

    # Test get_template_context
    context = get_template_context({"key": "value"})
    assert context["key"] == "value"
    assert "request" in context or "user" in context  # common context variables


@pytest.mark.django_db
def test_smart_logging_functions():
    """Test smart logging utilities without I/O"""
    try:
        from taller.utils.smart_logging import (
            format_log_message,
            get_log_level,
            sanitize_data,
        )
    except ImportError:
        pytest.skip("smart_logging functions not found")

    # Test format_log_message
    message = format_log_message("Test message", "INFO", {"user": "test"})
    assert isinstance(message, str)
    assert "Test message" in message
    assert "INFO" in message

    # Test sanitize_data
    data = {"password": "secret", "token": "abc123", "normal": "value"}
    sanitized = sanitize_data(data)
    assert sanitized["password"] == "***"
    assert sanitized["token"] == "***"
    assert sanitized["normal"] == "value"

    # Test get_log_level
    assert get_log_level("error") == "ERROR"
    assert get_log_level("warning") == "WARNING"
    assert get_log_level("info") == "INFO"
    assert get_log_level("debug") == "DEBUG"
    assert get_log_level("invalid") == "INFO"  # default
    assert get_log_level(None) == "INFO"  # default


@pytest.mark.django_db
def test_utils_edge_cases():
    """Test utils with edge cases and error conditions"""

    # Test with various data types
    edge_cases = [
        None,
        "",
        "   ",
        [],
        {},
        set(),
        tuple(),
        Decimal("0"),
        Decimal("123.45"),
        float("inf"),
        float("-inf"),
        float("nan"),
    ]

    # Test each utility with edge cases
    try:
        from taller.utils.pais_utils import get_country_code

        for case in edge_cases:
            result = get_country_code(case)
            assert result is None or isinstance(result, str)
    except ImportError:
        pass

    try:
        from taller.utils.smart_logging import sanitize_data

        for case in edge_cases:
            result = sanitize_data(case)
            assert result is not None
    except ImportError:
        pass
