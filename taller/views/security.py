from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from taller.auth.password_policy import set_user_must_change_password
from taller.forms.security import MandatoryPasswordChangeForm


@login_required
def force_password_change(request):
    if request.user.is_superuser:
        return redirect("/admin/")

    if request.method == "POST":
        form = MandatoryPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            set_user_must_change_password(user, False)
            update_session_auth_hash(request, user)
            messages.success(request, "Bienvenido. Tu contraseña personal quedó actualizada.")
            return redirect("/cl/es/dashboard/")
    else:
        form = MandatoryPasswordChangeForm(request.user)

    return render(request, "account/force_password_change.html", {"form": form})
