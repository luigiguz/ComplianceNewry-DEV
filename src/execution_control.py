import os
from datetime import datetime
from postgres_utils import get_postgres_connection
from cloud_logging import get_logger

def obtener_ultima_ejecucion():
    """
    Retorna la fecha de la última ejecución exitosa
    Retorna None si es la primera ejecución
    """
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT UltimaFechaCorreo
        FROM compliance_db."ComplianceEjecuciones" 
        WHERE Estado = 'COMPLETADO' 
        ORDER BY FechaEjecucion DESC 
        LIMIT 1
        """
        
        cursor.execute(query)
        resultado = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger = get_logger()
        
        if resultado and resultado[0]:
            logger.info(f"Última ejecución encontrada: {resultado[0]}")
            return resultado[0]
        else:
            logger.info("No se encontraron ejecuciones previas (primera ejecución)")
            return None
            
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error obteniendo última ejecución: {e}")
        return None  # En caso de error, asumir primera ejecución

def registrar_ejecucion(fecha_inicio, fecha_fin, correos_procesados, estado, duracion, modo):
    """
    Registra una nueva ejecución en PostgreSQL
    """
    try:
        ejecucion_id = f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        query = """
        INSERT INTO compliance_db."ComplianceEjecuciones" 
        (id, FechaEjecucion, UltimaFechaCorreo, CorreosProcesados, Estado, DuracionSegundos, Modo, FechaCreacion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        valores = (
            ejecucion_id,
            fecha_inicio,
            fecha_fin,
            correos_procesados,
            estado,
            duracion,
            modo,
            datetime.utcnow()
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger = get_logger()
        logger.info(f"Ejecución registrada: {ejecucion_id}")
        logger.info(f"Modo: {modo}, Correos procesados: {correos_procesados}, Duración: {duracion:.2f}s")
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error registrando ejecución: {e}")

def obtener_estadisticas_ejecuciones():
    """
    Obtiene estadísticas de las últimas ejecuciones
    """
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            COUNT(*) as total_ejecuciones,
            COUNT(CASE WHEN Estado = 'COMPLETADO' THEN 1 END) as exitosas,
            COUNT(CASE WHEN Estado = 'ERROR' THEN 1 END) as fallidas,
            AVG(DuracionSegundos) as duracion_promedio,
            MAX(FechaEjecucion) as ultima_ejecucion
        FROM compliance_db."ComplianceEjecuciones"
        WHERE FechaEjecucion >= NOW() - INTERVAL '30 days'
        """
        
        cursor.execute(query)
        resultado = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if resultado:
            return {
                'total_ejecuciones': resultado[0],
                'exitosas': resultado[1],
                'fallidas': resultado[2],
                'duracion_promedio': resultado[3],
                'ultima_ejecucion': resultado[4]
            }
        
        return None
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error obteniendo estadísticas: {e}")
        return None 