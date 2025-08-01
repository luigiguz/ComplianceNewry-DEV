-- Script para agregar columnas de control de ventana dinámica
-- Ejecutar en PostgreSQL para mejorar el control de ejecuciones

-- Agregar columna para registrar la fecha de inicio de la ventana procesada
ALTER TABLE compliance_db."ComplianceEjecuciones" 
ADD COLUMN "FechaInicioVentana" TIMESTAMP;

-- Agregar columna para registrar la fecha de fin de la ventana procesada
ALTER TABLE compliance_db."ComplianceEjecuciones" 
ADD COLUMN "FechaFinVentana" TIMESTAMP;

-- Agregar columna para el tipo de ventana procesada
ALTER TABLE compliance_db."ComplianceEjecuciones" 
ADD COLUMN "TipoVentana" VARCHAR(50) DEFAULT 'dinamica';

-- Agregar comentarios para documentar las nuevas columnas
COMMENT ON COLUMN compliance_db."ComplianceEjecuciones"."FechaInicioVentana" IS 'Fecha de inicio de la ventana de tiempo procesada';
COMMENT ON COLUMN compliance_db."ComplianceEjecuciones"."FechaFinVentana" IS 'Fecha de fin de la ventana de tiempo procesada';
COMMENT ON COLUMN compliance_db."ComplianceEjecuciones"."TipoVentana" IS 'Tipo de ventana: primera_ejecucion, ventana_dinamica';

-- Crear índice para mejorar consultas por ventana de tiempo
CREATE INDEX idx_compliance_ejecuciones_ventana 
ON compliance_db."ComplianceEjecuciones" ("FechaInicioVentana", "FechaFinVentana");

-- Verificar que las columnas se agregaron correctamente
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'compliance_db' 
AND table_name = 'ComplianceEjecuciones'
ORDER BY ordinal_position; 