import os

env = os.environ.get("EGARAGE_ENV", "dev").lower()
if env == "prod":
    from .prod import *
elif env == "min":
    from .min import *
else:
    from .dev import *
