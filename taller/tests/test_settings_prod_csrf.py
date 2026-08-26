"""
Tests de regresión para CSRF_TRUSTED_ORIGINS en gestion_taller/settings_prod.py.

Contexto (Fase 305/327/328): el módulo tenía DOS asignaciones a
CSRF_TRUSTED_ORIGINS. La segunda (hardcodeada, más abajo en el archivo)
pisaba silenciosamente la primera (env_list("DJANGO_CSRF_TRUSTED_ORIGINS", ...)),
dejando fuera cualquier dominio de tenant (ej. atlantareciclajes.cl) que solo
estuviera configurado en el .env de producción. Estos tests fijan la regla:
DJANGO_CSRF_TRUSTED_ORIGINS debe ser la única fuente de verdad.

Contexto (Fase 329/330): el DEFAULT de env_list(...) no incluía
monteazulspa.cl/www.monteazulspa.cl — si la env var faltara en el servidor,
MonteAzul perdía CSRF trust. Se corrigió el default; el test de ausencia de
env var abajo fija esa regla.

Contexto (Fase 331/332): además de MIDDLEWARE y
TEMPLATES[0]["OPTIONS"]["context_processors"], settings_prod.py también
reasigna TEMPLATES[0]["DIRS"] (líneas ~254/257) sobre el MISMO dict
compartido con gestion_taller.settings. El fixture de aislamiento restaura
las tres. El test de aislamiento usa "canarios" inyectados para demostrar
restauración real, no una coincidencia de que el valor recalculado converja
al mismo de antes.
"""

import ast
import contextlib
import importlib
from pathlib import Path

import pytest

import gestion_taller.settings as _base_settings

SETTINGS_PROD_PATH = (
    Path(__file__).resolve().parent.parent.parent / "gestion_taller" / "settings_prod.py"
)

DOMINIOS_REQUERIDOS = [
    "https://egarage.cl",
    "https://www.egarage.cl",
    "https://monteazulspa.cl",
    "https://www.monteazulspa.cl",
    "https://atlantareciclajes.cl",
    "https://www.atlantareciclajes.cl",
]

# ── Snapshot de origen ────────────────────────────────────────────────────────
#
# CRÍTICO: esta captura debe ocurrir aquí, a nivel de módulo, ANTES de que
# cualquier función de este archivo importe gestion_taller.settings_prod por
# primera vez. La PRIMERA vez que un módulo se importa, Python ejecuta TODO
# su código de nivel superior — incluidas las mutaciones in-situ que
# settings_prod.py hace sobre tres estructuras que son el MISMO objeto (o el
# mismo dict compartido) que expone gestion_taller.settings, no una copia:
#   - MIDDLEWARE.insert()/.append()                              (~líneas 306-311)
#   - TEMPLATES[0]["OPTIONS"]["context_processors"].append()     (~líneas 259-281)
#   - TEMPLATES[0]["DIRS"] = [...]  (reasignación de clave, no append) (~líneas 254-257)
# Auditado el archivo completo buscando append/extend/insert/remove/pop/
# clear/update/setdefault/+=/asignaciones por índice o clave: estas tres son
# las ÚNICAS mutaciones sobre objetos compartidos con gestion_taller.settings.
# (globals().pop("STATICFILES_STORAGE", None) en settings_prod.py solo afecta
# el namespace propio del módulo settings_prod, no un objeto compartido — ese
# nombre ni siquiera existe en gestion_taller.settings.)
#
# Si el snapshot se tomara DESPUÉS del primer import de settings_prod (p.ej.
# dentro de un fixture que ya lo importó antes de leer el "antes"), quedaría
# contaminado y cualquier "restauración" posterior fijaría el estado
# contaminado para el resto de la sesión de pytest — este archivo es el único
# en la suite que importa gestion_taller.settings_prod, así que capturarlo
# aquí es seguro. Cada baseline es una copia independiente (list(...)), no
# una referencia al objeto que se sigue mutando.
_MIDDLEWARE_BASELINE = list(_base_settings.MIDDLEWARE)
_CONTEXT_PROCESSORS_BASELINE = list(
    _base_settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
)
_DIRS_BASELINE = list(_base_settings.TEMPLATES[0]["DIRS"])


def _module_level_assignments(nombre_variable: str) -> list[int]:
    """Números de línea de asignaciones a *nombre_variable* a nivel de módulo."""
    tree = ast.parse(SETTINGS_PROD_PATH.read_text(encoding="utf-8"))
    return [
        node.lineno
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name) and target.id == nombre_variable
    ]


def test_csrf_trusted_origins_tiene_una_sola_asignacion_a_nivel_de_modulo():
    """Regresión directa del bug: una segunda asignación hardcodeada más abajo
    en el archivo pisaba el valor de env_list(DJANGO_CSRF_TRUSTED_ORIGINS, ...)
    sin que nada lo advirtiera."""
    asignaciones = _module_level_assignments("CSRF_TRUSTED_ORIGINS")
    assert len(asignaciones) == 1, (
        f"CSRF_TRUSTED_ORIGINS tiene {len(asignaciones)} asignaciones a nivel de "
        f"módulo en settings_prod.py (líneas {asignaciones}); debe haber exactamente "
        "una — env_list(DJANGO_CSRF_TRUSTED_ORIGINS, ...) es la única fuente de verdad."
    )


def test_csrf_trusted_origins_usa_env_list():
    """La única asignación debe seguir leyendo DJANGO_CSRF_TRUSTED_ORIGINS."""
    tree = ast.parse(SETTINGS_PROD_PATH.read_text(encoding="utf-8"))
    (assign,) = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name) and target.id == "CSRF_TRUSTED_ORIGINS"
    ]
    assert isinstance(assign.value, ast.Call)
    assert assign.value.func.id == "env_list"
    primer_arg = assign.value.args[0]
    assert isinstance(primer_arg, ast.Constant)
    assert primer_arg.value == "DJANGO_CSRF_TRUSTED_ORIGINS"


def _restaurar_estado_compartido() -> None:
    """Restaura MIDDLEWARE, context_processors y DIRS al snapshot de origen.

    MIDDLEWARE y context_processors se restauran por MUTACIÓN en sitio
    ([:] =) porque otros módulos (django.conf.settings, settings_test, etc.)
    pueden tener una referencia directa al MISMO objeto lista — rebindear el
    nombre no los alcanzaría. DIRS se restaura por reasignación de clave
    sobre el dict compartido TEMPLATES[0] (el mismo mecanismo que usa
    settings_prod.py para mutarlo), con una copia independiente del
    baseline para no dejar el atributo de clase apuntando al mismo objeto
    reutilizado entre llamadas.
    """
    _base_settings.MIDDLEWARE[:] = _MIDDLEWARE_BASELINE
    _base_settings.TEMPLATES[0]["OPTIONS"]["context_processors"][:] = (
        _CONTEXT_PROCESSORS_BASELINE
    )
    _base_settings.TEMPLATES[0]["DIRS"] = list(_DIRS_BASELINE)


@contextlib.contextmanager
def _reload_settings_prod_aislado(monkeypatch):
    """Context manager de bajo nivel: recarga settings_prod y garantiza la
    restauración del estado compartido al salir (incluso si el bloque `with`
    lanza). Compartido por el fixture de pytest de abajo y por el test de
    aislamiento, que necesita invocar la restauración explícitamente dentro
    de una única función de test (sin depender del orden de ejecución)."""
    import gestion_taller.settings_prod as settings_prod

    # Evita que un .env/.env.prod real en disco interfiera con el valor que
    # cada test controla explícitamente vía monkeypatch.setenv/delenv.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)

    def _reload():
        importlib.reload(settings_prod)
        return settings_prod

    try:
        yield _reload
    finally:
        _restaurar_estado_compartido()


@pytest.fixture
def reload_settings_prod(monkeypatch):
    """Fixture de pytest sobre _reload_settings_prod_aislado, para los tests
    que no necesitan inspeccionar el estado inmediatamente después de la
    restauración (basta con que quede limpio para el resto de la sesión)."""
    with _reload_settings_prod_aislado(monkeypatch) as reload_fn:
        yield reload_fn


@pytest.mark.parametrize(
    "env_value,esperado",
    [
        (
            "https://atlantareciclajes.cl,https://www.atlantareciclajes.cl",
            ["https://atlantareciclajes.cl", "https://www.atlantareciclajes.cl"],
        ),
        (
            "https://egarage.cl,https://www.egarage.cl,https://monteazulspa.cl,"
            "https://www.monteazulspa.cl,https://atlantareciclajes.cl,"
            "https://www.atlantareciclajes.cl",
            list(DOMINIOS_REQUERIDOS),
        ),
    ],
)
def test_csrf_trusted_origins_efectivo_respeta_env_var(
    monkeypatch, reload_settings_prod, env_value, esperado
):
    """Prueba dinámica: recarga el módulo real con DJANGO_CSRF_TRUSTED_ORIGINS
    seteado y confirma que el valor efectivo es EXACTAMENTE el del env — sin
    que ninguna reasignación posterior lo pise (antes del fix, esto fallaba:
    el valor efectivo siempre era la lista hardcodeada de egarage/monteazul)."""
    monkeypatch.setenv("DJANGO_CSRF_TRUSTED_ORIGINS", env_value)
    settings_prod = reload_settings_prod()
    assert settings_prod.CSRF_TRUSTED_ORIGINS == esperado


def test_csrf_trusted_origins_default_cuando_env_var_ausente(monkeypatch, reload_settings_prod):
    """Regresión Fase 329/330: si DJANGO_CSRF_TRUSTED_ORIGINS no está seteada
    en el entorno, el default de env_list() debe incluir igual los 6 orígenes
    requeridos (egarage, monteazul, atlanta) — antes del fix, el default
    omitía monteazulspa.cl/www.monteazulspa.cl y MonteAzul habría perdido
    CSRF trust en cuanto la env var faltara en el servidor."""
    monkeypatch.delenv("DJANGO_CSRF_TRUSTED_ORIGINS", raising=False)
    settings_prod = reload_settings_prod()
    assert settings_prod.CSRF_TRUSTED_ORIGINS == DOMINIOS_REQUERIDOS


def test_reload_settings_prod_restaura_estado_compartido(monkeypatch):
    """Demuestra RESTAURACIÓN real (no convergencia accidental) para las tres
    estructuras compartidas que settings_prod.py muta in-situ: MIDDLEWARE,
    context_processors y TEMPLATES[0]["DIRS"].

    Autocontenido: no depende de qué otros tests corrieron antes ni del
    orden de ejecución del archivo. Inyecta un marcador "canario" en cada
    estructura ANTES de recargar, para que la comprobación posterior no
    pueda pasar por casualidad — si la restauración fuera un no-op, el
    canario seguiría presente (MIDDLEWARE/context_processors) o el DIRS
    corrompido por settings_prod.py seguiría ahí en vez del baseline.
    """
    CANARIO_MW = "test_settings_prod_csrf.CANARIO_MIDDLEWARE"
    CANARIO_CP = "test_settings_prod_csrf.CANARIO_CONTEXT_PROCESSOR"
    CANARIO_DIRS = ["/canario/no-existe/settings_prod_csrf"]

    assert CANARIO_MW not in _MIDDLEWARE_BASELINE
    assert CANARIO_CP not in _CONTEXT_PROCESSORS_BASELINE
    assert _DIRS_BASELINE != CANARIO_DIRS
    assert "taller.middleware.lang_policy.LanguagePolicyMiddleware" not in _MIDDLEWARE_BASELINE

    with _reload_settings_prod_aislado(monkeypatch) as reload_fn:
        # Corrompe deliberadamente el estado compartido ANTES de recargar.
        _base_settings.MIDDLEWARE.append(CANARIO_MW)
        _base_settings.TEMPLATES[0]["OPTIONS"]["context_processors"].append(CANARIO_CP)
        _base_settings.TEMPLATES[0]["DIRS"] = list(CANARIO_DIRS)

        monkeypatch.delenv("DJANGO_CSRF_TRUSTED_ORIGINS", raising=False)
        reload_fn()

        # settings_prod.py solo AÑADE lo suyo si falta — no limpia el canario
        # de MIDDLEWARE/context_processors; confirma que el reload realmente
        # mutó estas listas compartidas (no son una copia inerte).
        assert CANARIO_MW in _base_settings.MIDDLEWARE
        assert "taller.middleware.lang_policy.LanguagePolicyMiddleware" in _base_settings.MIDDLEWARE
        assert CANARIO_CP in _base_settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
        # DIRS se REEMPLAZA por completo (no se anexa) — el canario debe
        # desaparecer, sustituido por el valor que settings_prod.py calcula.
        assert _base_settings.TEMPLATES[0]["DIRS"] != CANARIO_DIRS

    # Fuera del `with`: el finally de _reload_settings_prod_aislado ya corrió.
    # Verificación DENTRO de la misma función de test — sin depender de qué
    # otro test se ejecute después ni de orden alfabético.
    assert CANARIO_MW not in _base_settings.MIDDLEWARE
    assert CANARIO_CP not in _base_settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
    assert _base_settings.MIDDLEWARE == _MIDDLEWARE_BASELINE
    assert (
        _base_settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
        == _CONTEXT_PROCESSORS_BASELINE
    )
    assert _base_settings.TEMPLATES[0]["DIRS"] == _DIRS_BASELINE
