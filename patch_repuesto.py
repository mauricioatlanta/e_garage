from pathlib import Path

p = Path("taller/repuestos/views_cbv.py")
txt = p.read_text(encoding="utf-8")

if "def form_valid(self, form)" not in txt:

    new_block = """
    def form_valid(self, form):
        self.object = form.save()

        return_to = self.request.GET.get("return_to") or self.request.GET.get("next")

        if return_to:
            from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
            from django.shortcuts import redirect

            url_parts = list(urlparse(return_to))
            query = parse_qs(url_parts[4])

            query.update({
                "created_repuesto_id": self.object.id,
                "created_repuesto_nombre": self.object.nombre,
                "created_repuesto_codigo": getattr(self.object, "codigo", "") or "",
                "target_row": self.request.GET.get("target_row", ""),
            })

            url_parts[4] = urlencode(query, doseq=True)
            return redirect(urlunparse(url_parts))

        return super().form_valid(form)
"""

    txt = txt.replace("def get_initial(self):", "def get_initial(self):" + new_block)

    p.write_text(txt, encoding="utf-8")
    print("PATCH OK")

else:
    print("YA EXISTE")
