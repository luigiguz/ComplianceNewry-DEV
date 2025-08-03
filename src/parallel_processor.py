#!/usr/bin/env python3
"""
Módulo para procesamiento paralelo de correos
Implementa ThreadPoolExecutor para mejorar significativamente el rendimiento
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time
from typing import List, Dict, Any, Optional
from cloud_logging import get_logger
from gmail_utils import gmail_service_oauth, obtener_html_correo, guardar_html_en_storage, asunto_relevante
from vertex_utils import analizar_texto_vertex
from bigquery_utils import insertar_en_bigquery, correo_ya_procesado
from postgres_utils import insertar_en_postgresql, correo_ya_procesado_postgresql, insertar_tarea_postgresql
from config import CAMPOS_VERTEX, CONFIG_PARALELO, get_config
import json
import re
import email.utils

# Lock para operaciones thread-safe
db_lock = threading.Lock()
logger_lock = threading.Lock()

def convertir_fecha_correo(fecha_str):
    """Convierte la fecha del correo al formato requerido por BigQuery."""
    try:
        timestamp = email.utils.parsedate_to_datetime(fecha_str)
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        with logger_lock:
            logger = get_logger()
            logger.error(f"Error al convertir fecha '{fecha_str}': {e}")
        return None

def crear_datos_tarea(correo_id, resultado_json):
    """Crea los datos para insertar una nueva tarea basada en el análisis del correo."""
    fecha_actual = datetime.utcnow().isoformat()
    
    datos_tarea = {
        'CorreoId': correo_id,
        'TipoTarea': resultado_json.get('Clasificacion', 'No especificada'),
        'PrioridadId': resultado_json.get('PrioridadId', 1),
        'EstimacionDias': None,
        'Origen': 'GMAIL',
        'Objetivo': resultado_json.get('HowToFixIt', 'No especificada'),
        'MaterialAdicional': '',
        'EstadoId': 1,
        'FechaCreacion': fecha_actual,
        'FechaActualizacion': None
    }
    
    return datos_tarea

def procesar_correo_individual(correo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa un correo individual en un hilo separado.
    Thread-safe y con manejo de errores.
    """
    correo_id = correo_data['id']
    asunto = correo_data.get('subject', '')
    remitente = correo_data.get('from', '')
    destinatario = correo_data.get('to', '')
    fecha = correo_data.get('date', '')
    
    logger = get_logger()
    
    try:
        # Verificar si el asunto es relevante
        if not asunto_relevante(asunto):
            with logger_lock:
                logger.info(f"Correo ignorado por asunto irrelevante: {asunto}", 
                           correo_id=correo_id, asunto=asunto)
            return {
                'id': correo_id,
                'estado': 'ignorado',
                'razon': 'asunto_no_relevante',
                'error': None
            }
        
        # Verificar si ya fue procesado
        config = get_config()
        if correo_ya_procesado(correo_id, config.bigquery_table):
            with logger_lock:
                logger.info(f"Correo ya procesado, saltando", correo_id=correo_id)
            return {
                'id': correo_id,
                'estado': 'ya_procesado',
                'razon': 'duplicado',
                'error': None
            }
        
        # Obtener contenido del correo
        service = gmail_service_oauth()
        contenido = obtener_html_correo(service, correo_id)
        
        if not contenido:
            with logger_lock:
                logger.warning("No se pudo extraer contenido del correo", correo_id=correo_id)
            return {
                'id': correo_id,
                'estado': 'error',
                'razon': 'sin_contenido',
                'error': 'No se pudo extraer contenido'
            }
        
        # Guardar HTML en Cloud Storage
        with logger_lock:
            logger.info("Guardando HTML en Cloud Storage", correo_id=correo_id)
        
        correo_url = guardar_html_en_storage(
            contenido, correo_id, config.bucket_name, 
            asunto, remitente, destinatario, fecha
        )
        
        # Analizar con Vertex AI
        with logger_lock:
            logger.info("Enviando contenido a Vertex AI", correo_id=correo_id)
        
        resultado_vertex = analizar_texto_vertex(contenido)
        
        # Procesar respuesta de Vertex AI
        respuesta_limpia = resultado_vertex.strip()
        if respuesta_limpia.startswith('```'):
            partes = respuesta_limpia.split('```')
            for parte in partes:
                if '{' in parte and '}' in parte:
                    respuesta_limpia = parte.strip()
                    break
        
        # Extraer JSON
        start = respuesta_limpia.find('{')
        end = respuesta_limpia.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = respuesta_limpia[start:end+1]
        else:
            json_str = respuesta_limpia
        
        # Limpiar JSON
        json_str = re.sub(r':\s*,', ': "No especificada",', json_str)
        
        try:
            resultado_json = json.loads(json_str)
        except Exception as e:
            with logger_lock:
                logger.error(f"Error al parsear JSON de Vertex AI: {e}", correo_id=correo_id)
            resultado_json = {}
        
        # Preparar datos para BigQuery
        datos = {
            'CorreoId': correo_id,
            'FechaProcesamiento': datetime.utcnow().isoformat(),
            'Estado': resultado_json.get('Estado', 'No especificada'),
            'CorreoUrl': correo_url,
            'StoreAccess': correo_url
        }
        
        # Agregar campos de Vertex AI
        for campo in CAMPOS_VERTEX:
            if campo in ['PrioridadId', 'EstimacionDias']:
                continue
            valor = resultado_json.get(campo, 'No especificada')
            
            if campo == 'NotificationDate' and valor == 'No especificada':
                fecha_convertida = convertir_fecha_correo(fecha)
                datos[campo] = fecha_convertida if fecha_convertida else None
            elif campo == 'ComplianceDeadline' and valor == 'No especificada':
                datos[campo] = None
            else:
                datos[campo] = valor
        
        # Insertar en BigQuery (thread-safe)
        with db_lock:
            insertar_en_bigquery(datos, config.bigquery_table)
        
        with logger_lock:
            logger.info("Resultado insertado en BigQuery", correo_id=correo_id)
        
        # Insertar en PostgreSQL si no ha sido procesado
        with db_lock:
            if not correo_ya_procesado_postgresql(datos["CorreoId"]):
                insertar_en_postgresql(datos)
                
                # Crear tarea basada en el análisis
                datos_tarea = crear_datos_tarea(correo_id, resultado_json)
                insertar_tarea_postgresql(datos_tarea)
                
                with logger_lock:
                    logger.info("Resultado insertado en PostgreSQL y tarea creada", correo_id=correo_id)
            else:
                with logger_lock:
                    logger.info("Correo ya procesado en PostgreSQL", correo_id=correo_id)
        
        return {
            'id': correo_id,
            'estado': 'completado',
            'analisis': resultado_vertex,
            'error': None
        }
        
    except Exception as e:
        with logger_lock:
            logger.error(f"Error procesando correo {correo_id}: {e}", correo_id=correo_id)
        
        return {
            'id': correo_id,
            'estado': 'error',
            'razon': 'excepcion',
            'error': str(e)
        }

def procesar_correos_paralelo(correos: List[Dict[str, Any]], max_workers: int = None) -> List[Dict[str, Any]]:
    """
    Procesa correos en paralelo usando ThreadPoolExecutor.
    
    Args:
        correos: Lista de correos a procesar
        max_workers: Número máximo de hilos (usa CONFIG_PARALELO si no se especifica)
    
    Returns:
        Lista de resultados del procesamiento
    """
    if not correos:
        return []
    
    if max_workers is None:
        max_workers = CONFIG_PARALELO['max_workers']
    
    logger = get_logger()
    logger.info(f"Iniciando procesamiento paralelo con {max_workers} hilos")
    logger.info(f"Total de correos a procesar: {len(correos)}")
    
    resultados = []
    errores = []
    
    # Usar ThreadPoolExecutor para procesamiento paralelo
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todos los correos para procesamiento
        future_to_correo = {
            executor.submit(procesar_correo_individual, correo): correo 
            for correo in correos
        }
        
        # Recolectar resultados conforme terminan
        for future in as_completed(future_to_correo):
            correo = future_to_correo[future]
            
            try:
                resultado = future.result(timeout=CONFIG_PARALELO['timeout_por_correo'])
                resultados.append(resultado)
                
                # Log del progreso
                completados = len([r for r in resultados if r['estado'] == 'completado'])
                total = len(correos)
                logger.info(f"Progreso: {completados}/{total} correos completados")
                
            except Exception as e:
                error_result = {
                    'id': correo['id'],
                    'estado': 'error',
                    'razon': 'timeout_o_excepcion',
                    'error': str(e)
                }
                errores.append(error_result)
                logger.error(f"Error en procesamiento paralelo para correo {correo['id']}: {e}")
    
    # Resumen final
    completados = len([r for r in resultados if r['estado'] == 'completado'])
    ignorados = len([r for r in resultados if r['estado'] == 'ignorado'])
    ya_procesados = len([r for r in resultados if r['estado'] == 'ya_procesado'])
    total_errores = len(errores)
    
    logger.info(f"Procesamiento paralelo completado:")
    logger.info(f"  - Completados: {completados}")
    logger.info(f"  - Ignorados: {ignorados}")
    logger.info(f"  - Ya procesados: {ya_procesados}")
    logger.info(f"  - Errores: {total_errores}")
    
    # Combinar resultados y errores
    todos_resultados = resultados + errores
    
    return todos_resultados

def configurar_concurrencia(max_workers: int = None, timeout: int = None, retry_attempts: int = None):
    """
    Configura los parámetros de concurrencia para el procesamiento paralelo.
    
    Args:
        max_workers: Número máximo de hilos simultáneos
        timeout: Timeout por correo en segundos
        retry_attempts: Número de intentos por correo fallido
    """
    global CONFIG_PARALELO
    
    if max_workers is not None:
        CONFIG_PARALELO['max_workers'] = max_workers
    
    if timeout is not None:
        CONFIG_PARALELO['timeout_por_correo'] = timeout
    
    if retry_attempts is not None:
        CONFIG_PARALELO['retry_attempts'] = retry_attempts
    
    logger = get_logger()
    logger.info(f"Configuración de concurrencia actualizada: {CONFIG_PARALELO}")

def obtener_estadisticas_paralelo() -> Dict[str, Any]:
    """
    Retorna estadísticas de la configuración de paralelización.
    """
    return {
        'configuracion': CONFIG_PARALELO.copy(),
        'tiempo_estimado_por_correo': f"{CONFIG_PARALELO['timeout_por_correo']}s máximo"
    } 