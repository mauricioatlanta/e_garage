from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress, EmailConfirmation, EmailConfirmationHMAC
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.shortcuts import redirect
from django.views.decorators.http import require_POST


def _send_confirmation_compat(request, user, signup=False, email=None):
    target_email = (email or getattr(user, "email", "") or "").strip()
    if not target_email:
        return

    email_address = EmailAddress.objects.filter(user=user, email__iexact=target_email).first()
    if email_address is None:
        email_address = EmailAddress.objects.create(
            user=user,
            email=target_email,
            verified=False,
            primary=True,
        )

    confirmation = EmailConfirmationHMAC(email_address)
    adapter = get_adapter(request)
    adapter.send_confirmation_mail(request, confirmation, signup=signup)


@require_POST
def resend_signup_confirmation(request):
    """
    Reenvia el correo de confirmacion despues del registro sin autenticar al usuario.
    Evita revelar si el email existe para no exponer enumeracion de cuentas.
    """
    email = (request.POST.get("email") or request.session.get("pending_signup_email") or "").strip()
    country = (
        (request.POST.get("country") or request.session.get("pending_signup_country") or "CL")
        .strip()
        .upper()
    )
    lang = (
        (request.POST.get("lang") or request.session.get("pending_signup_lang") or "es")
        .strip()
        .lower()
    )
    if lang not in ("es", "en"):
        lang = "es"

    if email:
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            try:
                _send_confirmation_compat(request, user, signup=False, email=email)
            except Exception:
                # No bloquear UX por errores de proveedor de correo.
                pass

    messages.success(
        request,
        "Si el correo existe en el sistema, enviamos un nuevo enlace de confirmacion.",
    )
    return redirect(f"/{country.lower()}/{lang}/accounts/signup/")


def confirm_email_and_login(request, key):
    """
    Confirma email, autentica al usuario y redirige de forma country-aware.
    """
    confirmation = EmailConfirmationHMAC.from_key(key)
    if confirmation is None:
        confirmation = EmailConfirmation.objects.filter(key=key.lower()).first()

    if confirmation is None:
        messages.error(request, "El enlace de confirmacion es invalido o ya fue usado.")
        return redirect("/accounts/login/")

    email_address = confirmation.email_address
    confirmation.confirm(request)
    user = email_address.user

    if user and user.is_active:
        backend = "allauth.account.auth_backends.AuthenticationBackend"
        login(request, user, backend=backend)
        return redirect(get_adapter(request).get_login_redirect_url(request))

    messages.error(request, "No fue posible iniciar sesion tras confirmar tu correo.")
    return redirect("/accounts/login/")
