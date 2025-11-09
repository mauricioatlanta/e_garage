from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone


@login_required
def payment_chile(request):
    """
    Página de pago para Chile - Transferencia Bancaria
    """
    plan = request.GET.get("plan", "mensual")

    # Configuración de precios
    precios = {
        "mensual": {"valor": 10000, "dias": 30, "nombre": "Mensual"},
        "semestral": {"valor": 55000, "dias": 180, "nombre": "Semestral"},
        "anual": {"valor": 100000, "dias": 365, "nombre": "Anual"},
    }

    plan_info = precios.get(plan, precios["mensual"])

    # Datos bancarios
    datos_banco = {
        "banco": "BancoEstado",
        "tipo_cuenta": "Cuenta Vista",
        "titular": "Atlanta Reciclajes",
        "rut": "XX.XXX.XXX-X",  # ← Actualizar con RUT real
        "numero_cuenta": "XXXXXXXXXXXXX",  # ← Actualizar con número real
        "email_confirmacion": "pagos@atlantareciclajes.cl",
    }

    context = {
        "empresa": request.user.empresa,
        "plan": plan,
        "plan_info": plan_info,
        "datos_banco": datos_banco,
        "monto_pagar": plan_info["valor"],
        "referencia": f"eGarage-{request.user.empresa.id}-{plan}",
    }

    return render(request, "suscripcion/pago_chile.html", context)


@login_required
def payment_usa(request):
    """
    Página de pago para USA - PayPal
    """
    plan = request.GET.get("plan", "mensual")
    amount = request.GET.get("amount", "20")

    # Configuración de precios
    precios = {
        "mensual": {"valor": "20.00", "dias": 30, "nombre": "Monthly"},
        "semestral": {"valor": "110.00", "dias": 180, "nombre": "Semi-Annual"},
        "anual": {"valor": "200.00", "dias": 365, "nombre": "Annual"},
    }

    plan_info = precios.get(plan, precios["mensual"])

    # Datos PayPal
    paypal_config = {
        "business_email": "mauricioatlanta@gmail.com",
        "currency": "USD",
        "item_name": f'eGarage {plan_info["nombre"]} Subscription',
        "item_number": f"egarage-{plan}",
        "return_url": request.build_absolute_uri("/us/en/payment/success/"),
        "cancel_url": request.build_absolute_uri("/us/en/payment/cancel/"),
        "notify_url": request.build_absolute_uri("/us/en/payment/ipn/"),
    }

    context = {
        "empresa": request.user.empresa,
        "plan": plan,
        "plan_info": plan_info,
        "paypal_config": paypal_config,
        "amount": plan_info["valor"],
        "reference": f"eGarage-{request.user.empresa.id}-{plan}",
    }

    return render(request, "suscripcion/pago_usa.html", context)


@login_required
def subir_comprobante(request):
    """
    Subir comprobante de pago (especialmente para Chile)
    """
    if request.method == "POST":
        comprobante = request.FILES.get("comprobante")
        plan = request.POST.get("plan")
        monto = request.POST.get("monto")

        if comprobante:
            # Guardar comprobante
            empresa = request.user.empresa

            # Crear registro de pago pendiente
            from taller.models.pago import PagoPendiente

            pago = PagoPendiente.objects.create(
                empresa=empresa,
                plan=plan,
                monto=Decimal(monto),
                comprobante=comprobante,
                estado="pendiente",
                fecha_subida=timezone.now(),
            )

            messages.success(
                request,
                "✅ Comprobante recibido. Tu suscripción será activada en 24-48 horas después de verificar el pago.",
            )

            if empresa.pais == "CL":
                return redirect("/cl/es/dashboard/")
            else:
                return redirect("/us/en/dashboard/")

    return render(
        request,
        "suscripcion/subir_comprobante.html",
        {
            "empresa": request.user.empresa,
        },
    )


@login_required
def payment_success(request):
    """
    Callback de pago exitoso (PayPal)
    """
    # PayPal redirige aquí después de pago exitoso
    messages.success(
        request, "✅ Pago recibido! Tu suscripción será activada en las próximas horas."
    )

    if request.user.empresa.pais == "US":
        return redirect("/us/en/dashboard/")
    else:
        return redirect("/cl/es/dashboard/")


@login_required
def payment_cancel(request):
    """
    Usuario canceló el pago
    """
    messages.warning(
        request, "Pago cancelado. Puedes intentar nuevamente cuando lo desees."
    )

    if request.user.empresa.pais == "US":
        return redirect("/us/en/dashboard/")
    else:
        return redirect("/cl/es/dashboard/")
