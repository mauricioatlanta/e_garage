#!/usr/bin/env python
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def main():
    base_dir = Path(__file__).resolve().parent
    env_prod = base_dir / ".env.prod"

    if env_prod.exists():
        load_dotenv(env_prod, override=True)

    env_name = os.getenv("EGARAGE_ENV", "dev").lower()

    if env_name == "prod":
        os.environ["DJANGO_SETTINGS_MODULE"] = "gestion_taller.settings_prod"
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
