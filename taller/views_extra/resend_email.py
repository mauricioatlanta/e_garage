from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


class ResendEmailForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico", required=True)


def resend_email_view(request):
    if request.user.is_authenticated:
        # Usuario autenticado: reenviar a su email principal si no está verificado
        email_obj = EmailAddress.objects.filter(user=request.user, primary=True).first()
        if email_obj and not email_obj.verified:
            send_email_confirmation(request, request.user, email_obj.email)
            messages.success(
                request,
                "Se ha reenviado el correo de confirmación a tu email principal.",
            )
        else:
            messages.info(
                request,
                "Tu correo ya está verificado o no se encontró un email principal.",
            )
        return render(request, "account/resend_email.html", {"autenticado": True})
    else:
        # No autenticado: mostrar formulario
        if request.method == "POST":
            form = ResendEmailForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data["email"]
                User = get_user_model()
                user = User.objects.filter(email=email).first()
                if user:
                    email_obj = EmailAddress.objects.filter(
                        user=user, email=email
                    ).first()
                    if email_obj and not email_obj.verified:
                        send_email_confirmation(request, user, email)
                        messages.success(
                            request,
                            "Se ha reenviado el correo de confirmación si el email existe y no estaba verificado.",
                        )
                    else:
                        messages.info(
                            request,
                            "Ese correo ya está verificado o no existe en el sistema.",
                        )
                else:
                    messages.info(request, "No se encontró un usuario con ese correo.")
                return render(
                    request,
                    "account/resend_email.html",
                    {"form": form, "autenticado": False},
                )
        else:
            form = ResendEmailForm()
        return render(
            request, "account/resend_email.html", {"form": form, "autenticado": False}
        )
