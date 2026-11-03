import logging
from taller.models.public_page_view import PublicPageView, is_probable_bot
from taller.services.public_traffic_classifier import is_scanner_path, normalize_host, classify_traffic_channel
from taller.utils.smart_logging import get_client_ip
logger = logging.getLogger(__name__)
def _is_mobile(ua):
    u=(ua or '').lower()
    return 'mobile' in u or 'android' in u or 'iphone' in u
def _path_country(path):
    p=(path or '').strip('/').lower().split('/')
    if not p or not p[0]: return '',''
    if p[0]=='us':
        if len(p)>1 and p[1] in ('en','es'): return 'us', p[1]
        return 'us',''
    if len(p[0])==2: return p[0],''
    return '',''
def track_public_page(req, page_type='', country='', language=''):
    # Descartar rutas internas / administrativas
    p_req = getattr(req, "path", "") if "req" in locals() else ""
    if any(p_req.startswith(pref) for pref in ["/admin", "/staff", "/accounts", "/entrar-usa", "/dev-usa"]):
        return None

    # 0. Ignorar completamente accesos de superusuario y staff
    if getattr(req, "user", None) and req.user.is_authenticated and (req.user.is_superuser or req.user.is_staff):
        return None

    try:
        if req.method!='GET': return None
        path=(req.path or '')[:500]
        if is_scanner_path(path): return None
        raw=''
        try: raw=req.get_host()
        except: raw=''
        if not raw: raw=req.META.get('HTTP_X_FORWARDED_HOST','')
        if not raw: raw=req.META.get('HTTP_HOST','')
        if raw: raw=raw.split(',')[0].strip()
        host=normalize_host(raw or '')
        c_path,l_path=_path_country(path)
        if not country: country=c_path
        if not language: language=l_path
        if '_' in country: country=country.split('_')[0]
        country=(country or '')[:2].lower()
        language=(language or '')[:2].lower()
        ua=(req.META.get('HTTP_USER_AGENT') or '')[:800]
        ip=get_client_ip(req)
        is_bot=is_probable_bot(ua)
        is_mob=_is_mobile(ua)
        utm_src=(req.GET.get('utm_source') or '')[:200]
        utm_med=(req.GET.get('utm_medium') or '')[:200]
        utm_camp=(req.GET.get('utm_campaign') or '')[:200]
        ref_raw=(req.META.get('HTTP_REFERER') or '')
        chan=classify_traffic_channel(referrer=ref_raw, utm_source=utm_src)
        src=''
        if chan: src=str(chan).upper()[:50]
        elif utm_src: src=utm_src.upper()[:50]
        pv=PublicPageView.objects.create(
            path=path,
            host=host[:200],
            country=country[:8],
            language=language[:8],
            page_type=page_type[:50],
            referrer=(req.META.get('HTTP_REFERER') or '')[:1000],
            user_agent=ua,
            is_mobile=is_mob,
            is_bot=is_bot,
            source_label=src[:100],
            utm_source=utm_src,
            utm_medium=utm_med,
            utm_campaign=utm_camp,
            visitor_hash=ip[:100],
        )
        logger.error('[TRACK_OK] id=%s path=%s host=%s utm=%s c=%s', pv.id, pv.path, pv.host, pv.utm_source, pv.country)
        return pv
    except Exception as e:
        logger.error('[TRACK_FAIL] %s', e)
        return None
