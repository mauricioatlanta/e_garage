# Templates Canonical Repack

This archive was generated to organize your templates into a canonical, multi-country, multi-language structure:

templates/
  taller/
    common/
    cl/es/
    cl/en/
    us/es/
    us/en/
  _deprecated/           <- old or conflicting copies go here

## Rules
- Prefer Tailwind-based templates as canonical. Bootstrap variants were moved under `_deprecated/` when duplicates existed.
- Country & language were inferred from folder names and the template text.
- Document-related files were kept under `documentos/` when possible; others under their detected category or `common/`.

## Next Steps
1) Point your Django views to the canonical templates using a country+lang selector (see integration_samples/mixins.py).
2) Add the context processor (integration_samples/context_processors.py) to expose `country`, `company_settings`, `STATIC_VERSION`.
3) Enforce structure with `scripts/check_templates.py` in CI.
4) Remove files in `_deprecated/` once you've confirmed nothing depends on them.