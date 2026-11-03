from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
import pytz
from taller.services.public_analytics import get_analytics_stats
SCL_TZ=pytz.timezone('America/Santiago')
@staff_member_required
def public_analytics_dashboard(request):
    period=request.GET.get('period','day')
    days=int(request.GET.get('days','90'))
    if period not in ('day','week','month','year'): period='day'
    if period=='year' and days<365: days=800
    stats=get_analytics_stats(period=period, days=days)
    total=sum(s['total'] for s in stats)
    return render(request,'admin/public_analytics_dashboard.html',{'period':period,'days':days,'stats':stats,'total':total,'now_scl':timezone.now().astimezone(SCL_TZ)})
