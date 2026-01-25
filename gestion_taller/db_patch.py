"""
Monkey patch para forzar sslmode=disable en conexiones PostgreSQL locales.
Este archivo se importa en settings.py ANTES de que Django configure los backends.
"""

import os

# Establecer variable de entorno ANTES de cualquier importación de psycopg2
# Verificar si estamos usando PostgreSQL localhost
_db_host = os.getenv("DJANGO_DB_HOST") or os.getenv("DB_HOST", "")
_db_name = os.getenv("DJANGO_DB_NAME") or os.getenv("DB_NAME", "")

# Si hay nombre de BD configurado (indica PostgreSQL) y el host es localhost
if _db_name and (_db_host.lower() in ("localhost", "127.0.0.1", "::1") or not _db_host):
    os.environ["PGSSLMODE"] = "disable"
    os.environ.setdefault("PGSSL", "0")

    # También verificar DATABASE_URL
    _db_url = os.getenv("DATABASE_URL", "")
    if _db_url and ("postgres" in _db_url.lower() or "postgresql" in _db_url.lower()):
        import urllib.parse

        try:
            _parsed = urllib.parse.urlparse(_db_url)
            _host = _parsed.hostname or ""
            if _host.lower() in ("localhost", "127.0.0.1", "::1") or not _host:
                os.environ["PGSSLMODE"] = "disable"
                os.environ.setdefault("PGSSL", "0")
        except Exception:
            pass

# Parchear psycopg2.connect() directamente ANTES de que Django lo importe
# Esto intercepta la llamada a psycopg2.connect() y modifica los parámetros
# CRÍTICO: Este parche debe ejecutarse ANTES de que Django importe psycopg2
try:
    # Forzar variable de entorno ANTES de importar psycopg2
    _db_host_check = os.getenv("DJANGO_DB_HOST") or os.getenv("DB_HOST", "")
    _db_name_check = os.getenv("DJANGO_DB_NAME") or os.getenv("DB_NAME", "")
    if _db_name_check and (
        _db_host_check.lower() in ("localhost", "127.0.0.1", "::1") or not _db_host_check
    ):
        os.environ["PGSSLMODE"] = "disable"
        os.environ.setdefault("PGSSL", "0")

    import psycopg2

    _original_psycopg2_connect = psycopg2.connect

    # También parchear _connect si existe (función interna de psycopg2)
    _original_psycopg2__connect = getattr(psycopg2, "_connect", None)

    def _patched_psycopg2_connect(dsn=None, **kwargs):
        """Parche para psycopg2.connect() que fuerza sslmode=disable y host=127.0.0.1"""
        # Modificar kwargs si el host es localhost
        host = kwargs.get("host", "")

        # Intentar extraer host del DSN solo si no está en kwargs y el DSN es seguro de procesar
        if not host and dsn:
            try:
                if isinstance(dsn, str):
                    # Solo intentar si es string y no parece tener caracteres problemáticos
                    if "host=" in dsn:
                        import re

                        match = re.search(r"host=([^\s&]+)", dsn)
                        if match:
                            host = match.group(1).strip("'\"")
            except (UnicodeDecodeError, AttributeError, TypeError):
                # Si hay cualquier problema, no intentar procesar el DSN
                pass

        # Si el host es localhost o 127.0.0.1, forzar configuración
        # También si no hay host especificado (probablemente es localhost)
        if host in ("127.0.0.1", "localhost", "::1") or not host:
            # CRÍTICO: Forzar host a 127.0.0.1 (evita IPv6)
            kwargs["host"] = "127.0.0.1"

            # Asegurar que sslmode esté en disable
            if "sslmode" not in kwargs:
                kwargs["sslmode"] = "disable"

            # NO modificar el DSN - puede contener caracteres especiales en la contraseña
            # En su lugar, confiar en los kwargs que tienen prioridad sobre el DSN
            # Esto evita errores de UnicodeDecodeError

            # Establecer variable de entorno como respaldo
            os.environ["PGSSLMODE"] = "disable"
            os.environ.setdefault("PGSSL", "0")

            # Si hay un DSN, NO pasarlo para evitar problemas de codificación
            # Los kwargs tienen prioridad, así que psycopg2 usará los valores de kwargs
            dsn = None

        # Llamar a la función original
        # Si dsn es None, psycopg2 usará solo los kwargs
        # Los kwargs tienen prioridad sobre el DSN, así que si modificamos kwargs,
        # psycopg2 usará esos valores incluso si el DSN tiene valores diferentes
        try:
            return _original_psycopg2_connect(dsn=dsn, **kwargs)
        except UnicodeDecodeError:
            # Si aún hay error de codificación, intentar sin DSN (solo kwargs)
            return _original_psycopg2_connect(**kwargs)

    # Aplicar el parche a connect()
    psycopg2.connect = _patched_psycopg2_connect

    # También parchear _connect si existe (función interna)
    if _original_psycopg2__connect:

        def _patched_psycopg2__connect(dsn, connection_factory=None, **kwargs):
            """Parche para psycopg2._connect() que fuerza sslmode=disable y host=127.0.0.1"""
            # Extraer host del DSN si es posible
            host = kwargs.get("host", "")
            if not host and dsn:
                try:
                    if isinstance(dsn, str):
                        if "host=" in dsn:
                            import re

                            match = re.search(r"host=([^\s&]+)", dsn)
                            if match:
                                host = match.group(1).strip("'\"")
                except (UnicodeDecodeError, AttributeError, TypeError):
                    pass

            # Si el host es localhost, forzar configuración
            if host in ("127.0.0.1", "localhost", "::1") or not host:
                kwargs["host"] = "127.0.0.1"
                if "sslmode" not in kwargs:
                    kwargs["sslmode"] = "disable"
                os.environ["PGSSLMODE"] = "disable"
                # No pasar DSN si hay problemas de codificación
                dsn = None

            return _original_psycopg2__connect(dsn, connection_factory, **kwargs)

        psycopg2._connect = _patched_psycopg2__connect

except (ImportError, AttributeError):
    # psycopg2 no está disponible aún, se parcheará más tarde
    pass


def patch_postgresql_backend():
    """
    Aplica monkey patch al backend de PostgreSQL de Django.
    Se llama después de que Django está configurado.
    Parchea tanto get_connection_params como get_new_connection para máxima efectividad.
    """
    try:
        import django.db.backends.postgresql.base as pg_base

        # Parche 1: get_connection_params (se ejecuta primero)
        original_get_connection_params = pg_base.DatabaseWrapper.get_connection_params

        def patched_get_connection_params(self):
            """Parche para forzar sslmode=disable y host=127.0.0.1 en conexiones locales"""
            # Llamar al método original
            params = original_get_connection_params(self)

            # Obtener el host de los parámetros o de la configuración
            host = params.get("host", "")
            if not host:
                # Si no hay host en params, obtenerlo de settings_dict
                host = getattr(self, "settings_dict", {}).get("HOST", "")

            # Si el host es localhost o 127.0.0.1, forzar configuración SSL
            if host in ("127.0.0.1", "localhost", "::1") or not host:
                # CRÍTICO: Forzar host a 127.0.0.1 (evita IPv6)
                # Esto es esencial porque "localhost" puede resolverse a ::1 (IPv6)
                params["host"] = "127.0.0.1"

                # Asegurar que options existe y tiene sslmode=disable
                if "options" not in params:
                    params["options"] = {}

                # Forzar sslmode=disable explícitamente
                params["options"]["sslmode"] = "disable"

                # CRÍTICO: Eliminar el DSN si existe para evitar problemas de codificación
                # Los kwargs tienen prioridad, así que psycopg2 usará los valores de params
                # Esto evita que psycopg2 intente decodificar un DSN con caracteres especiales
                if "dsn" in params:
                    del params["dsn"]

                # CRÍTICO: Asegurar que todos los parámetros de string sean UTF-8 válidos
                # Esto evita errores de UnicodeDecodeError cuando psycopg2 procesa los parámetros
                for key in ["database", "user", "password", "host", "port"]:
                    if key in params and params[key] is not None:
                        try:
                            if isinstance(params[key], bytes):
                                # Si es bytes, decodificar a string UTF-8
                                params[key] = params[key].decode("utf-8", errors="replace")
                            elif not isinstance(params[key], str):
                                # Si no es string, convertir a string
                                params[key] = str(params[key])
                        except (UnicodeDecodeError, AttributeError):
                            # Si hay error, usar valor por defecto o saltar
                            pass

                # También establecer variable de entorno como respaldo
                # Esto es crítico porque psycopg2 puede leer esta variable
                os.environ["PGSSLMODE"] = "disable"
                os.environ.setdefault("PGSSL", "0")

            return params

        # Parche 2: get_new_connection (se ejecuta cuando realmente se conecta)
        original_get_new_connection = pg_base.DatabaseWrapper.get_new_connection

        def patched_get_new_connection(self, conn_params):
            """Parche final antes de que psycopg2.connect() sea llamado"""
            # CRÍTICO: Eliminar el DSN PRIMERO para evitar problemas de codificación
            # El DSN puede contener caracteres especiales que causan UnicodeDecodeError
            if "dsn" in conn_params:
                del conn_params["dsn"]

            # Obtener el host de los parámetros
            host = conn_params.get("host", "")

            # SIEMPRE verificar si es localhost y forzar 127.0.0.1
            # Esto es crítico porque psycopg2 puede resolver "localhost" a IPv6 (::1)
            if host in ("127.0.0.1", "localhost", "::1") or not host or host == "":
                # CRÍTICO: Forzar host a 127.0.0.1 (evita IPv6)
                conn_params["host"] = "127.0.0.1"

                # Asegurar que options existe y tiene sslmode=disable
                if "options" not in conn_params:
                    conn_params["options"] = {}

                # Forzar sslmode=disable explícitamente
                conn_params["options"]["sslmode"] = "disable"
                conn_params["options"]["client_encoding"] = "UTF8"

                # CRÍTICO: Asegurar que todos los parámetros de string sean UTF-8 válidos
                # Esto evita errores de UnicodeDecodeError cuando psycopg2 procesa los parámetros
                for key in ["dbname", "user", "password", "host", "port"]:
                    if key in conn_params and conn_params[key] is not None:
                        try:
                            if isinstance(conn_params[key], bytes):
                                # Si es bytes, decodificar a string UTF-8 con reemplazo de errores
                                conn_params[key] = conn_params[key].decode(
                                    "utf-8", errors="replace"
                                )
                            elif not isinstance(conn_params[key], str):
                                # Si no es string, convertir a string
                                conn_params[key] = str(conn_params[key])
                        except (UnicodeDecodeError, AttributeError, TypeError):
                            # Si hay error, intentar con latin-1 como fallback
                            try:
                                if isinstance(conn_params[key], bytes):
                                    conn_params[key] = conn_params[key].decode(
                                        "latin-1", errors="replace"
                                    )
                            except Exception:
                                # Si todo falla, saltar este parámetro
                                pass

                # También establecer variable de entorno como respaldo
                os.environ["PGSSLMODE"] = "disable"
                os.environ.setdefault("PGSSL", "0")

            # Llamar al método original con los parámetros modificados
            # Sin DSN, psycopg2 usará solo los kwargs de conn_params
            try:
                return original_get_new_connection(self, conn_params)
            except (UnicodeDecodeError, UnicodeEncodeError) as e:
                # Si aún hay error de codificación, reconstruir conn_params completamente
                # sin DSN y con codificación segura para todos los parámetros
                clean_params = {}
                for k, v in conn_params.items():
                    if k == "dsn":
                        continue
                    try:
                        if isinstance(v, bytes):
                            # Intentar UTF-8 primero, luego latin-1 como fallback
                            try:
                                clean_params[k] = v.decode("utf-8", errors="replace")
                            except (UnicodeDecodeError, AttributeError):
                                clean_params[k] = v.decode("latin-1", errors="replace")
                        elif isinstance(v, str):
                            # Si ya es string, asegurar que sea UTF-8 válido
                            clean_params[k] = v.encode("utf-8", errors="replace").decode("utf-8")
                        else:
                            clean_params[k] = v
                    except Exception:
                        # Si hay error, saltar este parámetro
                        continue
                return original_get_new_connection(self, clean_params)

        # Aplicar ambos parches
        pg_base.DatabaseWrapper.get_connection_params = patched_get_connection_params
        pg_base.DatabaseWrapper.get_new_connection = patched_get_new_connection
        return True
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"No se pudo aplicar parche SSL: {e}")
        return False


# Intentar aplicar el parche automáticamente si Django ya está configurado
# Esto es útil cuando el módulo se importa después de que Django está listo
try:
    import django

    if django.apps.apps.ready:
        # Django ya está configurado, aplicar el parche inmediatamente
        patch_postgresql_backend()
except (ImportError, AttributeError):
    # Django no está disponible o no está configurado aún
    pass
