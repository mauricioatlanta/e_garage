import pytest
from django.test import RequestFactory, override_settings
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_force_english_usa_middleware_smoke():
    """
    Test force_english_usa middleware with various Accept-Language headers.
    Should handle edge cases without crashing.
    """
    try:
        from taller.middleware.force_english_usa import ForceEnglishUSAMiddleware
    except ImportError:
        pytest.skip("force_english_usa middleware not available")
    
    rf = RequestFactory()
    middleware = ForceEnglishUSAMiddleware(lambda r: None)
    
    # Test with various Accept-Language headers
    test_cases = [
        # (accept_language, expected_behavior)
        ("*", "should handle wildcard"),
        ("xx-YY", "should handle invalid locale"),
        ("en-US,en;q=0.9", "should handle valid US English"),
        ("es-CL,es;q=0.9", "should handle Spanish"),
        ("", "should handle empty header"),
        ("invalid-locale", "should handle malformed locale"),
        ("en-US,es-CL,fr-FR", "should handle multiple locales"),
        ("en-US;q=0.8,es-CL;q=0.6", "should handle quality values"),
    ]
    
    for accept_language, description in test_cases:
        try:
            request = rf.get("/", HTTP_ACCEPT_LANGUAGE=accept_language)
            # Should not crash
            response = middleware(request)
            # Response should be None (pass-through) or a valid response
            assert response is None or hasattr(response, 'status_code'), f"Invalid response for {description}"
        except Exception as e:
            # If it crashes, that's a bug we want to catch
            pytest.fail(f"force_english_usa middleware crashed on {accept_language}: {e}")


@pytest.mark.django_db
def test_fix_language_middleware_smoke():
    """
    Test fix_language_middleware with various language scenarios.
    Should handle edge cases without crashing.
    """
    try:
        from taller.middleware.fix_language_middleware import FixLanguageMiddleware
    except ImportError:
        pytest.skip("fix_language_middleware not available")
    
    rf = RequestFactory()
    middleware = FixLanguageMiddleware(lambda r: None)
    
    # Test with various language scenarios
    test_cases = [
        # (accept_language, expected_behavior)
        ("*", "should handle wildcard"),
        ("xx-YY", "should handle invalid locale"),
        ("en-US", "should handle valid locale"),
        ("es-CL", "should handle Spanish locale"),
        ("", "should handle empty header"),
        ("invalid", "should handle malformed locale"),
        ("en-US,es-CL", "should handle multiple locales"),
        ("en-US;q=0.8", "should handle quality values"),
    ]
    
    for accept_language, description in test_cases:
        try:
            request = rf.get("/", HTTP_ACCEPT_LANGUAGE=accept_language)
            # Should not crash
            response = middleware(request)
            # Response should be None (pass-through) or a valid response
            assert response is None or hasattr(response, 'status_code'), f"Invalid response for {description}"
        except Exception as e:
            # If it crashes, that's a bug we want to catch
            pytest.fail(f"fix_language_middleware crashed on {accept_language}: {e}")


@pytest.mark.django_db
def test_language_middleware_with_user_context():
    """
    Test language middlewares with user context.
    """
    try:
        from taller.middleware.force_english_usa import ForceEnglishUSAMiddleware
        from taller.middleware.fix_language_middleware import FixLanguageMiddleware
    except ImportError:
        pytest.skip("Language middlewares not available")
    
    rf = RequestFactory()
    User = get_user_model()
    user = User.objects.create_user("testuser", "test@example.com", "password")
    
    # Test with user context
    test_cases = [
        ("en-US", "should handle US English with user"),
        ("es-CL", "should handle Spanish with user"),
        ("*", "should handle wildcard with user"),
        ("xx-YY", "should handle invalid locale with user"),
    ]
    
    for accept_language, description in test_cases:
        try:
            request = rf.get("/", HTTP_ACCEPT_LANGUAGE=accept_language)
            request.user = user
            
            # Test both middlewares
            for middleware_class, middleware_name in [
                (ForceEnglishUSAMiddleware, "force_english_usa"),
                (FixLanguageMiddleware, "fix_language_middleware"),
            ]:
                middleware = middleware_class(lambda r: None)
                response = middleware(request)
                assert response is None or hasattr(response, 'status_code'), f"Invalid response from {middleware_name} for {description}"
        except Exception as e:
            # If it crashes, that's a bug we want to catch
            pytest.fail(f"Language middleware crashed on {accept_language} with user: {e}")


@pytest.mark.django_db
def test_language_middleware_robustness():
    """
    Test language middlewares with problematic inputs.
    """
    try:
        from taller.middleware.force_english_usa import ForceEnglishUSAMiddleware
        from taller.middleware.fix_language_middleware import FixLanguageMiddleware
    except ImportError:
        pytest.skip("Language middlewares not available")
    
    rf = RequestFactory()
    
    # Test with problematic inputs
    problematic_inputs = [
        "en-US\x00",  # Null byte
        "en-US\x01\x02\x03",  # Control characters
        "en-US" + "x" * 1000,  # Very long string
        "en-US;q=0.8;q=0.9",  # Duplicate parameters
        "en-US;q=invalid",  # Invalid quality value
        "en-US;q=1.5",  # Quality > 1
        "en-US;q=-0.1",  # Negative quality
    ]
    
    for accept_language in problematic_inputs:
        try:
            request = rf.get("/", HTTP_ACCEPT_LANGUAGE=accept_language)
            
            # Test both middlewares
            for middleware_class, middleware_name in [
                (ForceEnglishUSAMiddleware, "force_english_usa"),
                (FixLanguageMiddleware, "fix_language_middleware"),
            ]:
                middleware = middleware_class(lambda r: None)
                response = middleware(request)
                # Should not crash, even with problematic inputs
                assert response is None or hasattr(response, 'status_code'), f"Invalid response from {middleware_name} for problematic input"
        except Exception as e:
            # If it crashes, that's a bug we want to catch
            pytest.fail(f"Language middleware crashed on problematic input '{accept_language}': {e}")
