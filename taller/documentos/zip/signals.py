"""
Signals legacy de LineaDocumento desactivados.

Motivo:
- LineaDocumento es un modelo legacy no gestionado (managed=False).
- La capa operativa actual usa LineaRepuesto, LineaServicio y LineaOtroServicio.
- Mantener este archivo sin receivers evita recálculos sobre una tabla inexistente.
"""
