"""
Módulo de documentos de eGarage

Este módulo maneja la creación, edición y gestión de documentos
(cotizaciones, órdenes de trabajo, facturas).

Modelos principales:
- Documento: Modelo principal (en taller.models.documento)
- DetalleDocumento: Líneas de items en documentos
- DocumentSequence: Secuencias de numeración
- LineaDocumento: Modelo legacy desactivado para migraciones/signals (managed=False, solo compatibilidad)
"""
