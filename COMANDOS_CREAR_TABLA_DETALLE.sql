-- SQL para crear la tabla taller_detalledocumento
-- Ejecutar en: python manage.py dbshell

CREATE TABLE IF NOT EXISTS "taller_detalledocumento" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "tipo_item" varchar(50) NOT NULL,
    "nombre" varchar(255) NOT NULL,
    "precio_venta" decimal NOT NULL,
    "cantidad" integer unsigned NOT NULL,
    "subtotal" decimal NULL,
    "documento_id" bigint NOT NULL REFERENCES "taller_documento" ("id") DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS "taller_detalledocumento_documento_id_idx" 
ON "taller_detalledocumento" ("documento_id");

