from pathlib import Path
import urllib.parse

p = Path("taller/common/mixins/context_return.py")
txt = p.read_text(encoding="utf-8")

old = """    def get_success_url(self):
        context_return = self.get_return_to()
        if context_return:
            return context_return
        default_success = getattr(self, "get_default_success_url", None)
        if callable(default_success):
            return default_success()
        return super().get_success_url()
"""

new = """    def get_success_url(self):
        context_return = self.get_return_to()

        payload = {}
        if hasattr(self, "get_created_object_payload"):
            try:
                payload = self.get_created_object_payload() or {}
            except Exception:
                payload = {}

        if context_return:
            if payload:
                parsed = urllib.parse.urlparse(context_return)
                qs = dict(urllib.parse.parse_qsl(parsed.query))
                qs.update({k: str(v) for k, v in payload.items() if v is not None})

                new_query = urllib.parse.urlencode(qs)
                return urllib.parse.urlunparse(parsed._replace(query=new_query))
            return context_return

        default_success = getattr(self, "get_default_success_url", None)
        if callable(default_success):
            return default_success()

        return super().get_success_url()
"""

if old not in txt:
    print("? BLOQUE ORIGINAL NO ENCONTRADO")
else:
    txt = txt.replace(old, new)
    p.write_text(txt, encoding="utf-8")
    print("? MIXIN PARCHEADO")
