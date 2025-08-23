-- Script SQL para agregar líneas de documento de prueba
-- Esto solucionará el problema de totales en $0

-- Primero verificamos qué documentos existen
SELECT id, numero, tipo, fecha FROM taller_documento ORDER BY id LIMIT 5;

-- Verificamos líneas existentes
SELECT COUNT(*) as total_lineas_repuesto FROM taller_linearepuesto;
SELECT COUNT(*) as total_lineas_servicio FROM taller_lineaservicio;

-- Si hay documentos pero no líneas, agregaremos líneas de prueba
-- Para el primer documento disponible

-- Insertar líneas de repuesto (ajustar documento_id según sea necesario)
INSERT INTO taller_linearepuesto (documento_id, codigo, nombre, cantidad, precio_unitario, descuento, repuesto_id, observaciones)
VALUES 
(1, 'REP001', 'Filtro de Aceite', 2, 15000.00, 0.00, NULL, 'Línea de prueba para totales'),
(1, 'REP002', 'Pastillas de Freno', 1, 45000.00, 10.00, NULL, 'Línea de prueba con descuento');

-- Insertar líneas de servicio
INSERT INTO taller_lineaservicio (documento_id, codigo, nombre, cantidad, precio_unitario, descuento, servicio_id, observaciones)
VALUES 
(1, 'SER001', 'Cambio de Aceite', 1, 25000.00, 0.00, NULL, 'Servicio de prueba'),
(1, 'SER002', 'Revisión General', 1, 35000.00, 5.00, NULL, 'Servicio con descuento');

-- Verificar los totales después de insertar
SELECT 
    d.id,
    d.numero,
    d.tipo,
    (SELECT COUNT(*) FROM taller_linearepuesto lr WHERE lr.documento_id = d.id) as lineas_repuesto,
    (SELECT COUNT(*) FROM taller_lineaservicio ls WHERE ls.documento_id = d.id) as lineas_servicio,
    (SELECT SUM(lr.cantidad * lr.precio_unitario * (1 - lr.descuento/100)) FROM taller_linearepuesto lr WHERE lr.documento_id = d.id) as total_repuestos,
    (SELECT SUM(ls.cantidad * ls.precio_unitario * (1 - ls.descuento/100)) FROM taller_lineaservicio ls WHERE ls.documento_id = d.id) as total_servicios
FROM taller_documento d
ORDER BY d.id
LIMIT 5;
