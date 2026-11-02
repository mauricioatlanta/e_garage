from django.shortcuts import render


def _deduce_country_lang(request):
    country = (
        request.session.get("pending_signup_country")
        or request.session.get("country")
        or request.GET.get("country")
    )

    if request.user.is_authenticated:
        empresa = getattr(request.user, "empresa", None)
        empresa_country = getattr(empresa, "pais", None) if empresa else None
        country = empresa_country or country

    path = (request.path or "").lower()
    if path.startswith("/us/"):
        country = "US"
    elif path.startswith("/cl/"):
        country = "CL"

    country = (country or "CL").strip().upper()
    lang = (
        request.session.get("pending_signup_lang")
        or request.GET.get("lang")
        or ("en" if country == "US" else "es")
    )
    lang = (lang or "es").strip().lower()
    if lang not in ("es", "en"):
        lang = "es"

    return country, lang


def confirm_email_pending_view(request):
    country, lang = _deduce_country_lang(request)
    email = (request.session.get("pending_signup_email") or "").strip()

    country_path = country.lower()
    login_url = f"/{country_path}/{lang}/accounts/login/"
    signup_url = f"/{country_path}/{lang}/accounts/signup/"
    if email:
        signup_url = f"{signup_url}?email={email}"

    context = {
        "country": country,
        "language_code": lang,
        "email": email,
        "login_url": login_url,
        "signup_url": signup_url,
    }
    return render(request, "account/confirm_email_pending.html", context)


def confirm_email_invalid_view(request):
    country, lang = _deduce_country_lang(request)
    email = (request.session.get("pending_signup_email") or "").strip()

    country_path = country.lower()
    login_url = f"/{country_path}/{lang}/accounts/login/"
    signup_url = f"/{country_path}/{lang}/accounts/signup/"
    if email:
        signup_url = f"{signup_url}?email={email}"

    context = {
        "country": country,
        "language_code": lang,
        "email": email,
        "login_url": login_url,
        "signup_url": signup_url,
    }
    return render(request, "account/confirm_email_invalid.html", context)
