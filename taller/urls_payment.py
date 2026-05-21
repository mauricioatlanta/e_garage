from django.urls import path

from taller.views_extra.payment_views import (
    flow_return,
    payment_cancel,
    payment_chile,
    payment_success,
    payment_usa,
    start_flow_payment,
    start_mp_payment,
    subir_comprobante,
)

urlpatterns = [
    # Chile - Transferencia Bancaria
    path("suscripcion/pago/chile/", payment_chile, name="payment_chile"),
    path("suscripcion/pago/cl/", payment_chile, name="pago_cl"),
    # USA - PayPal
    path("suscripcion/pago/usa/", payment_usa, name="payment_usa"),
    path("suscripcion/pago/us/", payment_usa, name="payment_us"),
    # Subir comprobante
    path("suscripcion/pago/comprobante/", subir_comprobante, name="subir_comprobante"),
    path("suscripcion/pago/upload/", subir_comprobante, name="upload_comprobante"),
    # Callbacks genéricos
    path("suscripcion/pago/success/", payment_success, name="payment_success"),
    path("suscripcion/pago/cancel/", payment_cancel, name="payment_cancel"),
    # Flow (Chile) - pasarela de pago online
    path("suscripcion/flow/iniciar/", start_flow_payment, name="start_flow_payment"),
    path("suscripcion/flow/retorno/", flow_return, name="flow_return"),
    # MercadoPago (Chile/MX/AR)
    path("suscripcion/mp/iniciar/", start_mp_payment, name="start_mp_payment"),
]
