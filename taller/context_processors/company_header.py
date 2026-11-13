from taller.utils.empresa import get_active_empresa

def company_header(request):
    c_code = getattr(request, 'country', None)
    if not c_code and hasattr(request, 'session'):
        c_code = request.session.get('support_country')
    if not c_code:
        c_code = 'cl'

    try:
        user = getattr(request, 'user', None)
        empresa = get_active_empresa(request) if user else None
    except Exception:
        empresa = None

    return {
        'country': c_code,
        'active_empresa': empresa,
    }
