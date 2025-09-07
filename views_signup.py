from django.shortcuts import redirect, render
from django.urls import reverse


def signup_country_select(request):
    return render(request, "account/signup_country_select.html")


def signup_chile(request):
    from django.contrib import messages
    from django.contrib.auth.models import User

    from taller.forms_signup import SignupChileForm
    from taller.models.perfil_usuario import PerfilUsuario

    if request.method == "POST":
        form = SignupChileForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            username = form.cleaned_data["username"]
            password1 = form.cleaned_data["password1"]
            password2 = form.cleaned_data["password2"]
            region = form.cleaned_data["region"]
            ciudad = form.cleaned_data["ciudad"]
            if password1 != password2:
                form.add_error("password2", "Las contraseñas no coinciden")
            elif User.objects.filter(username=username).exists():
                form.add_error("username", "El nombre de usuario ya existe")
            elif User.objects.filter(email=email).exists():
                form.add_error("email", "El correo ya está registrado")
            else:
                user = User.objects.create_user(
                    username=username, email=email, password=password1
                )
                user.save()
                PerfilUsuario.objects.create(
                    user=user, pais="CL", region=region, ciudad=ciudad
                )
                return render(request, "account/signup_success.html")
    else:
        form = SignupChileForm()
    return render(request, "account/signup.html", {"form": form, "country": "cl"})


def signup_usa(request):
    from django.contrib import messages
    from django.contrib.auth.models import User

    from taller.forms_signup import SignupUSAForm
    from taller.models.perfil_usuario import PerfilUsuario

    if request.method == "POST":
        form = SignupUSAForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            username = form.cleaned_data["username"]
            password1 = form.cleaned_data["password1"]
            password2 = form.cleaned_data["password2"]
            state = form.cleaned_data["state"]
            city = form.cleaned_data["city"]
            zipcode = form.cleaned_data["zipcode"]
            otra_ciudad = request.POST.get("otra_ciudad", "").strip()
            from taller.models.ubicacion import Ciudad, Estado

            if password1 != password2:
                form.add_error("password2", "Passwords do not match")
            elif User.objects.filter(username=username).exists():
                form.add_error("username", "Username already exists")
            elif User.objects.filter(email=email).exists():
                form.add_error("email", "Email already registered")
            else:
                # Si el usuario seleccionó "Otra" y escribió una ciudad nueva
                if (city == "otra" or city == "other") and otra_ciudad:
                    estado_obj = Estado.objects.filter(pk=state).first()
                    if estado_obj:
                        nueva_ciudad = Ciudad.objects.create(
                            nombre=otra_ciudad, estado=estado_obj
                        )
                        ciudad_obj = nueva_ciudad
                    else:
                        ciudad_obj = None
                else:
                    ciudad_obj = (
                        Ciudad.objects.filter(pk=city).first() if city else None
                    )
                user = User.objects.create_user(
                    username=username, email=email, password=password1
                )
                user.save()
                PerfilUsuario.objects.create(
                    user=user,
                    pais="US",
                    state=state,
                    ciudad=ciudad_obj,
                    zipcode=zipcode,
                )
                return render(request, "account/signup_success.html")
    else:
        form = SignupUSAForm()
    return render(request, "account/signup.html", {"form": form, "country": "us"})
