"""
Static files storage for production.

WhiteNoise's CompressedManifestStaticFilesStorage raises ValueError at *render time*
if any {% static %} path is missing from staticfiles.json (e.g. manifest.json not
collected after deploy). That takes down public pages (signup, bienvenida).

`manifest_strict = False` falls back to the logical path so templates still render.
Prefer fixing deploy: always run `collectstatic` so hashed assets and manifest stay in sync.
"""

from whitenoise.storage import CompressedManifestStaticFilesStorage


class LenientCompressedManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Same as WhiteNoise manifest storage, but do not 500 when an entry is missing."""

    manifest_strict = False
