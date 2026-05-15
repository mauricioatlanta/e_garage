import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
import django

django.setup()
from django.test import RequestFactory
from taller.views.country_aware_auth import CountryAwareLoginView
from django.contrib.auth.models import AnonymousUser

rf = RequestFactory()
req = rf.get("/us/en/accounts/login/")
req.user = AnonymousUser()
req.session = {}
view = CountryAwareLoginView.as_view()
resp = view(req)
resp.render()
html = resp.content.decode("utf-8")
print('name="country"' in html)
idx = html.find('name="country"')
print(idx)
if idx != -1:
    print(html[idx - 80 : idx + 80])
