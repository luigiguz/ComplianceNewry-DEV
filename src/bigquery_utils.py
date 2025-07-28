import os
from google.cloud import bigquery
from config import get_config

def insertar_en_bigquery(datos, tabla):
    """Inserta los datos en la tabla de BigQuery especificada."""
    client = bigquery.Client()
    errors = client.insert_rows_json(tabla, [datos])
    if errors:
        raise Exception(f'Errores al insertar en BigQuery: {errors}')
    return True


def correo_ya_procesado(CorreoId, tabla):
    """Verifica si un correo ya ha sido procesado en BigQuery."""
    client = bigquery.Client()
    query = f"""
        SELECT COUNT(*) as total
        FROM `{tabla}`
        WHERE CorreoId = @CorreoId
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("CorreoId", "STRING", CorreoId)
        ]
    )
    query_job = client.query(query, job_config=job_config)
    result = query_job.result()
    for row in result:
        return row.total > 0
    return False 