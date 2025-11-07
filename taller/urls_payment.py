from django.urls import path

from taller.views_extra.payment_views import (
    payment_cancel,
    payment_chile,
    payment_success,
    payment_usa,
    subir_comprobante,
)

app_name = "payment"

urlpatterns = [
    # Chile - Transferencia Bancaria
    path("chile/", payment_chile, name="payment_chile"),
    path("cl/pago/", payment_chile, name="pago_cl"),
    
    # USA - PayPal
    path("usa/", payment_usa, name="payment_usa"),
    path("us/payment/", payment_usa, name="payment_us"),
    
    # Subir comprobante (principalmente Chile)
    path("upload/", subir_comprobante, name="subir_comprobante"),
    path("comprobante/", subir_comprobante, name="upload_comprobante"),
    
    # Callbacks PayPal
    path("success/", payment_success, name="success"),
    path("cancel/", payment_cancel, name="cancel"),
]

