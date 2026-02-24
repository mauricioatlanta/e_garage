# tools/dump_us_form_local.py
import os
import re
import sys
from pathlib import Path

# ✅ Asegura que el ROOT del proyecto esté en sys.path (E:\projecto\e_garage)
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

# ✅ Usa el mismo settings module que usa tu manage.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402


def main():
    setup_test_environment()

    User = get_user_model()
    u = User.objects.filter(is_superuser=True, is_active=True).first()
    if not u:
        print("ERROR: no superuser activo encontrado")
        return

    c = Client()
    c.force_login(u)

    r = c.get("/us/documentos/form/", follow=True)

    print("STATUS:", r.status_code)
    print("REDIRECT_CHAIN:", getattr(r, "redirect_chain", None))

    html = r.content.decode("utf-8", "ignore")
    Path("us_form_local.html").write_text(html, encoding="utf-8")

    # href/src con comillas simples o dobles
    refs = re.findall(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", html, flags=re.I)
    static_refs = sorted({x for x in refs if x.startswith("/static/")})

    Path("us_form_local_static.txt").write_text("\n".join(static_refs), encoding="utf-8")

    print("HTML_LEN:", len(html))
    print("STATIC_COUNT:", len(static_refs))

    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    title = re.sub(r"\s+", " ", m.group(1)).strip() if m else "NO_TITLE"
    print("TITLE:", title[:160])

    tpl_names = [t.name for t in getattr(r, "templates", []) if getattr(t, "name", None)]
    print("TEMPLATE_NAMES_COUNT:", len(tpl_names))
    for name in tpl_names[:40]:
        print("-", name)


if __name__ == "__main__":
    main()
