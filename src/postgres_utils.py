import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from config import get_config
load_dotenv()

def get_postgres_connection():
    """Devuelve una conexión a la base de datos PostgreSQL usando la configuración del sistema."""
    config = get_config()
    
    # Verificar que la configuración de PostgreSQL esté completa
    if not all([config.pg_host, config.pg_user, config.pg_password, config.pg_database]):
        raise ValueError("Configuración de PostgreSQL incompleta. Verifica PG_HOST, PG_USER, PG_PASSWORD, PG_DATABASE")
    
    return psycopg2.connect(
        host=config.pg_host,
        port=config.pg_port,
        user=config.pg_user,
        password=config.pg_password,
        dbname=config.pg_database
    )

def insertar_en_postgresql(datos):
    """Inserta los datos en la tabla compliance_db.compliance_issues en PostgreSQL."""
    conn = get_postgres_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                insert_query = sql.SQL("""
                    INSERT INTO compliance_db."ComplianceIssues" (
                        "CorreoId", "FechaProcesamiento", "Estado", "AppId", "Version", "Motivo", "Clasificacion", "HowToFixIt", "PlataformaOrigen", "CorreoUrl", "Guideline", "RejectInformation", "NotificationDate", "ComplianceDeadline", "StoreLink", "StoreAccess"
                    ) VALUES (
                        %(CorreoId)s, %(FechaProcesamiento)s, %(Estado)s, %(AppId)s, %(Version)s, %(Motivo)s, %(Clasificacion)s, %(HowToFixIt)s, %(PlataformaOrigen)s, %(CorreoUrl)s, %(Guideline)s, %(RejectInformation)s, %(NotificationDate)s, %(ComplianceDeadline)s, %(StoreLink)s, %(StoreAccess)s
                    )
                    ON CONFLICT ("CorreoId") DO NOTHING
                """)
                cur.execute(insert_query, datos)
    finally:
        conn.close()
    return True


def correo_ya_procesado_postgresql(correo_id):
    """Verifica si un correo_id ya existe en compliance_db.ComplianceIssues en PostgreSQL."""
    conn = get_postgres_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM compliance_db."ComplianceIssues" WHERE "CorreoId" = %s
                    """,
                    (correo_id,)
                )
                result = cur.fetchone()
                return result[0] > 0
    finally:
        conn.close()

def insertar_tarea_postgresql(datos_correo):
    """Inserta una nueva tarea en la tabla compliance_db.ComplianceTasks en PostgreSQL."""
    conn = get_postgres_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                insert_query = sql.SQL("""
                    INSERT INTO compliance_db."ComplianceTasks" (
                        "CorreoId", "TipoTarea", "PrioridadId", "EstimacionDias", 
                        "Origen", "Objetivo", "MaterialAdicional", "EstadoId", 
                        "FechaCreacion", "FechaActualizacion"
                    ) VALUES (
                        %(CorreoId)s, %(TipoTarea)s, %(PrioridadId)s, %(EstimacionDias)s,
                        %(Origen)s, %(Objetivo)s, %(MaterialAdicional)s, %(EstadoId)s,
                        %(FechaCreacion)s, %(FechaActualizacion)s
                    )
                """)
                cur.execute(insert_query, datos_correo)
    finally:
        conn.close()
    return True 