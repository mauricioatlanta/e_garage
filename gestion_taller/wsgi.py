import os
import sys
import io

# Windows: forzar UTF-8 en stdout/stderr ANTES de cargar Django.
# Evita UnicodeEncodeError (ej. emoji ✅) al escribir en cp1252.
if os.name == "nt":
    os.environ.setdefault("PYTHONUTF8", "1")
    try:
        # Reconfigurar stdout y stderr con UTF-8 y manejo de errores
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        # Si reconfigure no está disponible (Python < 3.7), usar TextIOWrapper
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass
    except Exception:
        pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

from django.core.wsgi import get_wsgi_application

# Obtener la aplicación WSGI base
_django_app = get_wsgi_application()


class UTF8ErrorWrapper:
    """
    Wrapper para wsgi.errors que convierte automáticamente a UTF-8
    y maneja errores de encoding de forma segura.
    """

    def __init__(self, original_stream):
        self.original_stream = original_stream

    def write(self, s):
        """Escribe al stream, manejando errores de encoding."""
        try:
            # Si es un string, asegurarse de que se puede escribir
            if isinstance(s, str):
                # Intentar escribir directamente
                self.original_stream.write(s)
            else:
                # Si es bytes, decodificar primero a UTF-8 y luego escribir
                decoded = s.decode("utf-8", errors="replace")
                self.original_stream.write(decoded)
        except UnicodeEncodeError:
            # Si falla por encoding, convertir el string a ASCII seguro
            try:
                if isinstance(s, str):
                    # Reemplazar caracteres problemáticos
                    safe_s = s.encode("ascii", errors="replace").decode("ascii")
                    self.original_stream.write(safe_s)
                else:
                    # Si es bytes, decodificar con reemplazo
                    safe_s = (
                        s.decode("utf-8", errors="replace")
                        .encode("ascii", errors="replace")
                        .decode("ascii")
                    )
                    self.original_stream.write(safe_s)
            except Exception:
                # Último recurso: escribir un mensaje genérico
                try:
                    self.original_stream.write(
                        "[Encoding error: message contains unsupported characters]\n"
                    )
                except Exception:
                    pass
        except Exception:
            # Cualquier otro error: intentar escribir al stream original
            try:
                if hasattr(self.original_stream, "write"):
                    if isinstance(s, str):
                        # Convertir a bytes UTF-8 y luego escribir
                        self.original_stream.buffer.write(s.encode("utf-8", errors="replace"))
                    else:
                        self.original_stream.write(s)
            except Exception:
                pass

    def flush(self):
        """Flush del stream."""
        try:
            if hasattr(self.original_stream, "flush"):
                self.original_stream.flush()
        except Exception:
            pass

    def __getattr__(self, name):
        """Delegar otros atributos al stream original."""
        return getattr(self.original_stream, name)


def _patch_wsgi_errors(environ):
    """
    Parchea wsgi.errors para usar UTF-8 en Windows.
    Esto evita UnicodeEncodeError cuando Django intenta escribir emojis o otros caracteres Unicode.
    """
    if os.name == "nt" and "wsgi.errors" in environ:
        wsgi_errors = environ["wsgi.errors"]
        # Si wsgi.errors tiene encoding cp1252, parchearlo
        if hasattr(wsgi_errors, "encoding"):
            encoding = getattr(wsgi_errors, "encoding", "").lower()
            if encoding == "cp1252" or (encoding and encoding not in ("utf-8", "utf8")):
                try:
                    # Guardar el método write original
                    original_write = wsgi_errors.write

                    def safe_write(s):
                        """Write method que maneja errores de encoding."""
                        try:
                            return original_write(s)
                        except UnicodeEncodeError:
                            # Si falla, convertir a ASCII seguro
                            try:
                                if isinstance(s, str):
                                    # Reemplazar caracteres no-ASCII
                                    safe_s = s.encode("ascii", errors="replace").decode("ascii")
                                    return original_write(safe_s)
                                else:
                                    # Si es bytes, decodificar y convertir
                                    decoded = s.decode("utf-8", errors="replace")
                                    safe_s = decoded.encode("ascii", errors="replace").decode(
                                        "ascii"
                                    )
                                    return original_write(safe_s)
                            except Exception:
                                # Si todo falla, escribir un mensaje genérico
                                try:
                                    original_write(
                                        "[Encoding error: message contains unsupported characters]\n"
                                    )
                                except Exception:
                                    pass

                    # Reemplazar el método write
                    wsgi_errors.write = safe_write
                except Exception:
                    # Si falla, intentar envolverlo
                    try:
                        environ["wsgi.errors"] = UTF8ErrorWrapper(wsgi_errors)
                    except Exception:
                        pass


def application(environ, start_response):
    """
    Wrapper de la aplicación WSGI que parchea wsgi.errors para usar UTF-8.
    """
    # Parchear wsgi.errors ANTES de que Django lo use
    _patch_wsgi_errors(environ)
    # Delegar a la aplicación Django
    return _django_app(environ, start_response)
