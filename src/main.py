from flask import Request
from gmail_utils import gmail_service_oauth, listar_correos
from execution_control import obtener_ultima_ejecucion, registrar_ejecucion
from cloud_logging import get_logger
from config import get_config, validate_and_print_config
from parallel_processor import procesar_correos_paralelo, configurar_concurrencia, obtener_estadisticas_paralelo
import os
from datetime import datetime
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai")

# Las funciones convertir_fecha_correo y crear_datos_tarea se movieron a parallel_processor.py

def main(request: Request):
    """Función principal para Cloud Function con procesamiento paralelo."""
    tiempo_inicio = time.time()
    logger = get_logger()
    
    logger.log_execution_start(mode="detecting", max_results=0)
    
    # Validar configuración
    if not validate_and_print_config():
        logger.error("Configuración inválida")
        return {
            'error': 'Configuración inválida', 
            'status': 'error',
            'resultados': [],
            'modo': 'error',
            'correos_procesados': 0,
            'duracion_segundos': 0
        }
    
    # Obtener configuración
    config = get_config()
    
    # Mostrar estadísticas de paralelización
    stats_paralelo = obtener_estadisticas_paralelo()
    logger.info(f"Configuración de paralelización: {stats_paralelo}")
    
    # Detectar automáticamente el tipo de ejecución
    ultima_ejecucion = obtener_ultima_ejecucion()
    
    if ultima_ejecucion:
        # Ejecución dinámica: desde la última ejecución hasta ahora
        fecha_desde = ultima_ejecucion
        max_results = 200  # Límite razonable para ventanas dinámicas
        modo = "ventana_dinamica"
        logger.info(f"Modo: Ventana dinámica desde {fecha_desde}")
    else:
        # Primera ejecución: ventana de 24 horas hacia atrás
        from datetime import timedelta
        fecha_desde = datetime.utcnow() - timedelta(hours=24)
        max_results = 200
        modo = "primera_ejecucion"
        logger.info(f"Modo: Primera ejecución - ventana de 24h desde {fecha_desde}")
    
    # Obtener lista de correos
    service = gmail_service_oauth()
    logger.info("Servicio de Gmail inicializado")
    
    correos = listar_correos(service, max_results=max_results, fecha_desde=fecha_desde)
    logger.info(f"Correos encontrados: {len(correos)}", correos_count=len(correos))
    
    logger.log_execution_start(mode=modo, max_results=max_results, fecha_desde=fecha_desde)
    
    # Procesar correos en paralelo
    logger.info("Iniciando procesamiento paralelo de correos")
    resultados_paralelo = procesar_correos_paralelo(correos)
    
    # Filtrar solo los correos completados exitosamente
    resultados_completados = [
        r for r in resultados_paralelo 
        if r['estado'] == 'completado' and 'analisis' in r
    ]
    
    # Calcular duración y registrar ejecución
    tiempo_fin = time.time()
    duracion = tiempo_fin - tiempo_inicio
    
    # Obtener fecha del último correo procesado (si hay)
    ultima_fecha_correo = None
    if correos and len(correos) > 0:
        ultimo_correo = correos[0]  # El más reciente
        fecha_ultimo = ultimo_correo.get('date', '')
        if fecha_ultimo:
            from parallel_processor import convertir_fecha_correo
            ultima_fecha_correo = convertir_fecha_correo(fecha_ultimo)
    
    # Registrar la ejecución con control de ventana dinámica
    registrar_ejecucion(
        fecha_inicio=datetime.utcnow(),
        fecha_fin=ultima_fecha_correo,
        correos_procesados=len(correos),
        estado='COMPLETADO',
        duracion=duracion,
        modo=modo,
        fecha_inicio_ventana=fecha_desde,
        fecha_fin_ventana=datetime.utcnow()
    )
    
    # Estadísticas finales
    completados = len([r for r in resultados_paralelo if r['estado'] == 'completado'])
    ignorados = len([r for r in resultados_paralelo if r['estado'] == 'ignorado'])
    ya_procesados = len([r for r in resultados_paralelo if r['estado'] == 'ya_procesado'])
    errores = len([r for r in resultados_paralelo if r['estado'] == 'error'])
    
    logger.info(f"Procesamiento paralelo finalizado:")
    logger.info(f"  - Completados: {completados}")
    logger.info(f"  - Ignorados: {ignorados}")
    logger.info(f"  - Ya procesados: {ya_procesados}")
    logger.info(f"  - Errores: {errores}")
    logger.info(f"  - Duración total: {duracion:.2f} segundos")
    
    logger.log_execution_end(
        mode=modo,
        correos_procesados=len(correos),
        duracion=duracion,
        estado='COMPLETADO'
    )
    
    return {
        'resultados': resultados_completados, 
        'modo': modo, 
        'correos_procesados': len(correos),
        'duracion_segundos': duracion,
        'estadisticas_paralelo': {
            'completados': completados,
            'ignorados': ignorados,
            'ya_procesados': ya_procesados,
            'errores': errores
        }
    } 