import pytest
from decimal import Decimal

@pytest.mark.django_db
def test_moneda_formats():
    """Test moneda template tag with various formats and edge cases"""
    try:
        from taller.templatetags.moneda import moneda
    except ImportError:
        pytest.skip("moneda template tag not found")
    
    # Test CLP format
    assert moneda(1000, "CLP") == "$1.000"
    assert moneda(1000000, "CLP") == "$1.000.000"
    assert moneda(0, "CLP") == "$0"
    
    # Test USD format
    assert moneda(1000, "USD") == "$1,000.00"
    assert moneda(1000000, "USD") == "$1,000,000.00"
    assert moneda(0, "USD") == "$0.00"
    
    # Test edge cases
    assert moneda(None, "CLP") == "$0"
    assert moneda("", "CLP") == "$0"
    assert moneda("invalid", "CLP") == "$0"
    
    # Test decimal precision
    assert moneda(Decimal("1234.56"), "USD") == "$1,234.56"
    assert moneda(Decimal("1234.567"), "USD") == "$1,234.57"  # rounded

@pytest.mark.django_db
def test_qs_tools_operations():
    """Test qs_tools template tag operations"""
    try:
        from taller.templatetags.qs_tools import qs_add, qs_remove
    except ImportError:
        pytest.skip("qs_tools template tags not found")
    
    # Test qs_add
    assert qs_add("?page=1", "sort", "name") == "?page=1&sort=name"
    assert qs_add("", "filter", "active") == "?filter=active"
    assert qs_add("?existing=value", "new", "test") == "?existing=value&new=test"
    
    # Test qs_remove
    assert qs_remove("?page=1&sort=name", "sort") == "?page=1"
    assert qs_remove("?filter=active&page=2", "filter") == "?page=2"
    assert qs_remove("?single=value", "single") == ""
    
    # Test edge cases
    assert qs_add(None, "key", "value") == "?key=value"
    assert qs_remove(None, "key") == ""
    assert qs_add("", "", "") == ""
    assert qs_remove("", "") == ""

@pytest.mark.django_db
def test_timezone_tags_formatting():
    """Test timezone template tags with various inputs"""
    try:
        from taller.templatetags.timezone_tags import format_datetime, localize_time
    except ImportError:
        pytest.skip("timezone template tags not found")
    
    # Test format_datetime
    test_date = "2025-01-15T10:30:00Z"
    formatted = format_datetime(test_date, "America/Santiago")
    assert isinstance(formatted, str)
    assert len(formatted) > 0
    
    # Test localize_time
    localized = localize_time(test_date, "America/New_York")
    assert isinstance(localized, str)
    assert len(localized) > 0
    
    # Test edge cases
    assert format_datetime(None, "UTC") == ""
    assert format_datetime("", "UTC") == ""
    assert format_datetime("invalid", "UTC") == ""
    assert localize_time(None, "UTC") == ""
    assert localize_time("", "UTC") == ""
