"""
HTTP assertion utilities for testing Django applications.

Provides centralized helpers for validating HTTP responses, especially
for handling redirects from country middleware.
"""


def assert_ok_or_redirect(resp, expected_redirect_suffix=None):
    """
    Assert that a response is either successful (200/201) or a redirect (302).

    Args:
        resp: Django test client response
        expected_redirect_suffix: Expected suffix for redirect Location header

    Raises:
        AssertionError: If response is not 200/201/302 or redirect destination is wrong
    """
    if resp.status_code in (200, 201):
        return

    assert (
        resp.status_code == 302
    ), f"Expected 200/201/302, got {resp.status_code}: {resp.content}"

    if expected_redirect_suffix:
        location = resp.headers.get("Location", "")
        assert location.endswith(
            expected_redirect_suffix
        ), f"Redirect to {location} doesn't end with {expected_redirect_suffix}"


def assert_json_response(resp, expected_status_codes=(200, 201)):
    """
    Assert that a response is successful and contains valid JSON.

    Args:
        resp: Django test client response
        expected_status_codes: Tuple of acceptable status codes

    Returns:
        dict: Parsed JSON response

    Raises:
        AssertionError: If response is not successful or JSON is invalid
    """
    assert (
        resp.status_code in expected_status_codes
    ), f"Expected {expected_status_codes}, got {resp.status_code}: {resp.content}"

    try:
        return resp.json()
    except ValueError as e:
        raise AssertionError(
            f"Response is not valid JSON: {e}. Content: {resp.content}"
        )


def assert_redirect_preserves_querystring(
    resp, expected_base_path, expected_params=None
):
    """
    Assert that a redirect preserves querystring parameters.

    Args:
        resp: Django test client response (should be 302)
        expected_base_path: Expected base path in Location header
        expected_params: Dict of expected query parameters

    Raises:
        AssertionError: If redirect doesn't preserve querystring
    """
    assert resp.status_code == 302, f"Expected 302 redirect, got {resp.status_code}"

    location = resp.headers.get("Location", "")
    assert location.startswith(
        expected_base_path
    ), f"Redirect to {location} doesn't start with {expected_base_path}"

    if expected_params:
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(location)
        actual_params = parse_qs(parsed.query)

        for key, expected_value in expected_params.items():
            assert key in actual_params, f"Missing query parameter: {key}"
            actual_value = actual_params[key][0] if actual_params[key] else ""
            assert (
                actual_value == expected_value
            ), f"Query param {key}: expected {expected_value}, got {actual_value}"
