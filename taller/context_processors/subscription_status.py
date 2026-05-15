from taller.services.subscription_access_service import SubscriptionAccessService


def subscription_status(request):
    empresa = getattr(request, "empresa", None)
    return {
        "subscription_state": getattr(request, "subscription_state", "active"),
        "subscription_access_reason": getattr(request, "subscription_access_reason", None),
        "billing_renew_url": getattr(
            request,
            "billing_renew_url",
            SubscriptionAccessService.get_billing_url(empresa),
        ),
    }
