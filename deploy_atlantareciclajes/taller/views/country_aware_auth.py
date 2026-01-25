from pathlib import Path
from allauth.account.views import LoginView
from django.conf import settings
from django.template.response import TemplateResponse
from django.utils.translation import get_language, activate, gettext_lazy
from django.template.loader import get_template, select_template
from django.template import TemplateDoesNotExist

# Debug: Log cuando se importa el módulo
print("[DEBUG] taller.views.country_aware_auth module loaded")


class CountryAwareLoginView(LoginView):
    """
    Implementación de LoginView que detecta el país/idioma antes de delegar en allauth.
    Siempre usa templates que existen, con fallback seguro.
    """

    # CRÍTICO: Establecer template_name como None para forzar que get_template_names() se use
    # Esto previene que allauth construya nombres dinámicos basados en el idioma activo
    template_name = None

    def __init__(self, *args, **kwargs):
        """
        CRÍTICO: Interceptar __init__ para asegurar que template_name se establezca correctamente.
        """
        # CRÍTICO: Remover template_name de kwargs si existe para evitar que allauth lo use
        if "template_name" in kwargs:
            del kwargs["template_name"]
        super().__init__(*args, **kwargs)
        # Forzar que template_name sea None para que get_template_names() se use
        self.template_name = None
        # También establecer self.request = None temporalmente (se establecerá en dispatch)
        self.request = None

    def dispatch(self, request, *args, **kwargs):
        # CRÍTICO: El middleware CountryDetectionMiddleware ya detectó el país
        # y activó el idioma correspondiente. Solo verificamos que esté correcto.

        # Asegurar que el país esté correcto desde el GET parameter si existe (PRIORIDAD MÁXIMA)
        country_param = request.GET.get("country", "").upper().strip()
        if country_param:
            from taller.utils import get_normalized_country
            from taller.middleware.country_detection import CountryDetectionMiddleware

            country = get_normalized_country(country_param)
            request.country = country
            # Re-activar el idioma correcto
            lang_full = CountryDetectionMiddleware.COUNTRY_LANGUAGE_MAP.get(country, "es")
            activate(lang_full)
            # CRÍTICO: Establecer LANGUAGE_CODE en request para que Django lo use
            request.LANGUAGE_CODE = lang_full
            if hasattr(request, "session"):
                request.session["preferred_country"] = country
                request.session["django_language"] = lang_full
            print(
                f"[CountryAwareLoginView.dispatch] GET param detected - Country: {country}, Language: {lang_full}, Activated: {get_language()}"
            )
        else:
            country = getattr(request, "country", "CL")
            lang_full = get_language() or "es"

        # CRÍTICO: Establecer self.request ANTES de llamar a _get_template_name()
        self.request = request

        # Establecer el template_name ANTES de que Django/allauth intente usarlo
        # Esto asegura que get_template_names() se use correctamente
        # O mejor aún, establecer los candidatos directamente aquí
        template_candidates = self._get_template_name()
        self.template_name = template_candidates  # Establecer explícitamente los candidatos

        # Debug logging
        print(f"[CountryAwareLoginView.dispatch] Final Country: {country}, Language: {lang_full}")
        print(f"[CountryAwareLoginView.dispatch] Request path: {request.path}")
        print(f"[CountryAwareLoginView.dispatch] GET params: {request.GET}")
        if hasattr(request, "session"):
            print(
                f"[CountryAwareLoginView.dispatch] Session preferred_country: {request.session.get('preferred_country', 'N/A')}"
            )
            print(
                f"[CountryAwareLoginView.dispatch] Session django_language: {request.session.get('django_language', 'N/A')}"
            )
        print(f"[CountryAwareLoginView.dispatch] Template candidates set: {template_candidates}")
        print(f"[CountryAwareLoginView.dispatch] Current get_language(): {get_language()}")
        print(
            f"[CountryAwareLoginView.dispatch] request.LANGUAGE_CODE: {getattr(request, 'LANGUAGE_CODE', 'NOT SET')}"
        )

        # NO llamar a super().dispatch() para evitar que allauth construya el template
        # En su lugar, manejar el dispatch nosotros mismos
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    # Nota: La detección de país ahora la hace CountryDetectionMiddleware
    # El país está disponible en request.country y request.country_code

    # ------------------------------------------------------------------ #
    # Overrides de LoginView
    # ------------------------------------------------------------------ #
    def get_template_names(self):
        """
        CRÍTICO: Sobrescribir get_template_names() para que retorne el template correcto
        basado en país e idioma, no el que allauth construye.
        Retorna una lista de candidatos que Django probará en orden.

        Este método DEBE retornar una lista ANTES de que allauth/Django construya el template name.
        """
        # Si no tenemos request todavía (puede pasar en __init__), retornar lista vacía temporalmente
        if not hasattr(self, "request") or self.request is None:
            print(f"[get_template_names] WARNING: request is None, returning fallback list")
            return ["account/login.html"]  # Fallback seguro

        # CRÍTICO: Asegurar que el país e idioma estén correctos antes de obtener templates
        country_param = self.request.GET.get("country", "").upper().strip()
        if country_param:
            from taller.utils import get_normalized_country
            from taller.middleware.country_detection import CountryDetectionMiddleware

            country = get_normalized_country(country_param)
            self.request.country = country
            lang_full = CountryDetectionMiddleware.COUNTRY_LANGUAGE_MAP.get(country, "es")
            # CRÍTICO: Activar el idioma ANTES de construir el template name
            activate(lang_full)
            # CRÍTICO: También establecer en request para que Django lo use
            self.request.LANGUAGE_CODE = lang_full
            if hasattr(self.request, "session"):
                self.request.session["preferred_country"] = country
                self.request.session["django_language"] = lang_full
            print(
                f"[get_template_names] GET param detected - Country: {country}, Language: {lang_full}, Activated: {get_language()}"
            )

        # Usar el mismo método que _get_template_name() para consistencia
        candidates = self._get_template_name()

        # CRÍTICO: Asegurar que self.template_name esté establecido como lista
        # para que Django use esta lista en lugar de construir el template name
        self.template_name = candidates

        print(f"[get_template_names] Returning candidates: {candidates}")
        print(
            f"[get_template_names] self.template_name set to: {self.template_name} (type: {type(self.template_name)})"
        )
        return candidates

    def get(self, request, *args, **kwargs):
        """
        Sobrescribir get() para asegurar que el template se resuelva correctamente.
        """
        from django.contrib.auth import REDIRECT_FIELD_NAME
        from django.utils.http import url_has_allowed_host_and_scheme

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        # Manejar redirect field
        redirect_field_name = self.redirect_field_name
        redirect_field_value = request.GET.get(redirect_field_name)
        redirect_to = redirect_field_value if redirect_field_value else None

        if redirect_to:
            redirect_to = url_has_allowed_host_and_scheme(redirect_to, None)

        if not redirect_to:
            redirect_to = self.get_success_url()

        # Obtener contexto
        context = self.get_context_data(form=form)
        context[redirect_field_name] = redirect_to

        # Usar render_to_response que usará la lista de candidatos
        return self.render_to_response(context)

    def form_valid(self, form):
        """
        Sobrescribir form_valid() para evitar que allauth construya el template name.
        """
        from django.contrib.auth import login
        from allauth.account.utils import perform_login
        from allauth.account import app_settings as account_settings
        from allauth.exceptions import ImmediateHttpResponse

        # Obtener el usuario
        user = form.user

        # Obtener email_verification de la configuración de allauth
        # Si el atributo existe en la instancia, usarlo; si no, usar la configuración
        email_verification = getattr(self, "email_verification", None)
        if email_verification is None:
            email_verification = account_settings.EMAIL_VERIFICATION

        # Realizar el login usando allauth
        try:
            ret = perform_login(
                self.request,
                user,
                email_verification=email_verification,
                redirect_url=self.get_success_url(),
                signal_kwargs={"signal_kwargs": {"to": user}},
            )
            return ret
        except ImmediateHttpResponse as e:
            return e.response

    def post(self, request, *args, **kwargs):
        """
        Sobrescribir post() para asegurar que el template se resuelva correctamente.
        """
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            return self.form_valid(form)
        else:
            # Si el formulario no es válido, renderizar con errores
            context = self.get_context_data(form=form)

            # Usar render_to_response que usará la lista de candidatos
            return self.render_to_response(context)

    def _get_template_name(self):
        """
        Obtiene el nombre del template correcto basado en país e idioma.
        Retorna una lista de candidatos para que Django pruebe automáticamente.
        Usa una jerarquía escalable:
        1. Específico por país/idioma: {country}/{lang}/account/login.html
        2. Por país: {country}/account/login.html
        3. Por idioma: {lang}/account/login.html
        4. Template base: account/login.html
        """
        # CRÍTICO: Priorizar el parámetro GET sobre request.country
        # porque puede haber sido sobrescrito por otros middlewares
        country_param = self.request.GET.get("country", "").upper().strip()
        if country_param:
            from taller.utils import get_normalized_country

            country = get_normalized_country(country_param)
        else:
            country = getattr(self.request, "country", "CL").upper()

        # Obtener idioma correspondiente al país detectado
        from taller.middleware.country_detection import CountryDetectionMiddleware

        lang_full = CountryDetectionMiddleware.COUNTRY_LANGUAGE_MAP.get(country, "es")
        # Extraer el código de idioma base (pt-br -> pt, es -> es)
        lang = lang_full.split("-")[0] if "-" in lang_full else lang_full

        # Debug logging
        print(f"[_get_template_name] Country: {country}, Lang: {lang} (full: {lang_full})")
        print(f"[_get_template_name] request.country: {getattr(self.request, 'country', 'N/A')}")
        print(f"[_get_template_name] GET country param: {country_param}")

        # Lista de candidatos en orden de prioridad (de más específico a más general)
        # Django intentará cada uno hasta encontrar el que existe
        candidates = [
            f"{country.lower()}/{lang}/account/login.html",  # 1. Específico: cl/es/account/login.html
            f"{country.lower()}/account/login.html",  # 2. Por país: cl/account/login.html
            f"{lang}/account/login.html",  # 3. Por idioma: es/account/login.html
            "account/login.html",  # 4. Template base (plan B definitivo)
        ]

        print(f"[_get_template_name] Candidates: {candidates}")
        return candidates

    def render_to_response(self, context, **response_kwargs):
        """
        Sobrescribir render_to_response para forzar el uso del template correcto
        independientemente de lo que allauth intente hacer.
        Usa una lista de candidatos para que Django pruebe automáticamente.
        """
        # CRÍTICO: Asegurar que el país e idioma estén correctos antes de obtener templates
        country_param = self.request.GET.get("country", "").upper().strip()
        if country_param:
            from taller.utils import get_normalized_country
            from taller.middleware.country_detection import CountryDetectionMiddleware

            country = get_normalized_country(country_param)
            self.request.country = country
            lang_full = CountryDetectionMiddleware.COUNTRY_LANGUAGE_MAP.get(country, "es")
            activate(lang_full)
            self.request.session["preferred_country"] = country
            self.request.session["django_language"] = lang_full
            print(
                f"[render_to_response] Forced country: {country}, language: {lang_full} from GET param"
            )

        # Obtener lista de candidatos usando el método centralizado
        template_candidates = self._get_template_name()

        # Establecer template_name para consistencia
        self.template_name = template_candidates

        # Debug logging
        print(f"[render_to_response] Template candidates: {template_candidates}")
        print(f"[render_to_response] Current language: {get_language()}")
        print(f"[render_to_response] Request country: {getattr(self.request, 'country', 'N/A')}")
        print(f"[render_to_response] self.template_name type: {type(self.template_name)}")
        print(f"[render_to_response] self.template_name value: {self.template_name}")

        # CRÍTICO: Usar select_template directamente para forzar el uso de nuestra lista
        from django.template.loader import select_template

        template = select_template(template_candidates)

        # Crear TemplateResponse con el template seleccionado
        response = TemplateResponse(self.request, template, context, **response_kwargs)
        return response

    def get_context_data(self, **kwargs):
        # CRÍTICO: NO llamar a super().get_context_data() porque puede hacer que allauth
        # construya el template name antes de que nosotros lo establezcamos.
        # En su lugar, construir el contexto nosotros mismos basado en allauth
        from allauth.account.views import LoginView as AllauthLoginView

        # Llamar al get_context_data de la clase base (LoginView) pero SIN super()
        # para evitar que allauth construya el template name
        # En su lugar, construir el contexto manualmente
        context = {}

        # Agregar el formulario si existe
        if "form" not in kwargs:
            form_class = self.get_form_class()
            kwargs["form"] = self.get_form(form_class)

        # Agregar campos estándar de allauth (sin llamar a super())
        context.update(
            {
                "form": kwargs.get("form"),
                "redirect_field_name": self.redirect_field_name,
                "redirect_field_value": self.request.GET.get(self.redirect_field_name, ""),
                "can_signup": True,  # Asumir que el signup está habilitado
            }
        )

        # CRÍTICO: Asegurar que template_name esté establecido como lista ANTES de retornar
        # para que Django use get_template_names() si es necesario
        if self.template_name is None or isinstance(self.template_name, str):
            template_candidates = self._get_template_name()
            self.template_name = template_candidates
            print(f"[get_context_data] Forced template_name to list: {template_candidates}")

        # Agregar nuestros campos personalizados
        context["country"] = getattr(self.request, "country", "CL")
        context["LANGUAGE_CODE"] = get_language() or "es"
        context["debug"] = True

        return context


# Vista funcional como alternativa
def country_aware_login(request, *args, **kwargs):
    """
    Wrapper funcional para mantener compatibilidad con las URLs actuales.
    CRÍTICO: Forzar template_name=None aquí también para evitar que allauth construya el template name.
    """
    # Debug logging al inicio
    print(f"[country_aware_login] ENTRY - Path: {request.path}, GET: {request.GET}")
    print(f"[country_aware_login] Current language: {get_language()}")
    print(
        f"[country_aware_login] Cookie django_language: {request.COOKIES.get('django_language', 'NOT SET')}"
    )

    # CRÍTICO: Asegurar que el país e idioma estén correctos ANTES de crear la vista
    country_param = request.GET.get("country", "").upper().strip()
    print(f"[country_aware_login] Country param from GET: '{country_param}'")

    if country_param:
        from taller.utils import get_normalized_country
        from taller.middleware.country_detection import CountryDetectionMiddleware

        country = get_normalized_country(country_param)
        request.country = country
        lang_full = CountryDetectionMiddleware.COUNTRY_LANGUAGE_MAP.get(country, "es")

        # CRÍTICO: Activar el idioma ANTES de crear la vista
        from django.utils.translation import activate

        activate(lang_full)

        # CRÍTICO: Actualizar sesión
        request.session["preferred_country"] = country
        request.session["django_language"] = lang_full

        # CRÍTICO: También establecer LANGUAGE_CODE en request para que Django lo use
        request.LANGUAGE_CODE = lang_full

        print(
            f"[country_aware_login] GET param detected - Country: {country}, Language: {lang_full}"
        )
        print(f"[country_aware_login] Language activated: {get_language()}")
        print(f"[country_aware_login] request.LANGUAGE_CODE set to: {lang_full}")
    else:
        print(
            f"[country_aware_login] No country param, using request.country: {getattr(request, 'country', 'N/A')}"
        )

    # CRÍTICO: Crear la vista SIN pasar template_name para evitar que allauth lo use
    # CountryAwareLoginView.__init__() ya se asegura de que template_name sea None
    print(f"[country_aware_login] Creating view (no template_name parameter)")
    view = CountryAwareLoginView.as_view()
    print(f"[country_aware_login] View created, calling it now")
    result = view(request, *args, **kwargs)

    # CRÍTICO: Si el resultado es una respuesta, eliminar la cookie django_language problemática
    # y establecer una nueva con el idioma correcto
    if hasattr(result, "set_cookie") and country_param:
        from taller.middleware.country_detection import CountryDetectionMiddleware

        lang_full = CountryDetectionMiddleware.COUNTRY_LANGUAGE_MAP.get(country, "es")
        # Eliminar la cookie antigua si existe
        result.delete_cookie("django_language", path="/")
        # Establecer la cookie nueva con el idioma correcto
        result.set_cookie("django_language", lang_full, max_age=365 * 24 * 60 * 60, path="/")
        print(f"[country_aware_login] Cookie django_language set to: {lang_full}")

    print(f"[country_aware_login] View returned, type: {type(result)}")
    return result
