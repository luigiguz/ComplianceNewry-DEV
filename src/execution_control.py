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
        SELECT ultimafechacorreo
        FROM compliance_db."ComplianceEjecuciones" 
        WHERE estado = 'COMPLETADO' 
        ORDER BY fechaejecucion DESC 
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

def registrar_ejecucion(fecha_inicio, fecha_fin, correos_procesados, estado, duracion, modo, fecha_inicio_ventana=None, fecha_fin_ventana=None):
    """
    Registra una nueva ejecución en PostgreSQL con control de ventana dinámica
    """
    try:
        ejecucion_id = f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        query = """
        INSERT INTO compliance_db."ComplianceEjecuciones" 
        (id, fechaejecucion, ultimafechacorreo, correosprocesados, estado, duracionsegundos, modo, fechacreacion, "FechaInicioVentana", "FechaFinVentana", "TipoVentana")
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Determinar tipo de ventana basado en el modo
        tipo_ventana = 'primera_ejecucion' if modo == 'primera_ejecucion' else 'ventana_dinamica'
        
        valores = (
            ejecucion_id,
            fecha_inicio,
            fecha_fin,
            correos_procesados,
            estado,
            duracion,
            modo,
            datetime.utcnow(),
            fecha_inicio_ventana,
            fecha_fin_ventana,
            tipo_ventana
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
            COUNT(CASE WHEN estado = 'COMPLETADO' THEN 1 END) as exitosas,
            COUNT(CASE WHEN estado = 'ERROR' THEN 1 END) as fallidas,
            AVG(duracionsegundos) as duracion_promedio,
            MAX(fechaejecucion) as ultima_ejecucion
        FROM compliance_db."ComplianceEjecuciones"
        WHERE fechaejecucion >= NOW() - INTERVAL '30 days'
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