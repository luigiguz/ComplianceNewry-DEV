from dotenv import load_dotenv
load_dotenv()
from flask import Request
from gmail_utils import gmail_service_oauth, listar_correos, obtener_html_correo, guardar_html_en_storage, asunto_relevante
from vertex_utils import analizar_texto_vertex
from bigquery_utils import insertar_en_bigquery, correo_ya_procesado
from postgres_utils import insertar_en_postgresql, correo_ya_procesado_postgresql, insertar_tarea_postgresql
from config import PALABRAS_CLAVE, CAMPOS_VERTEX, get_config, validate_and_print_config
import os
from datetime import datetime
import json
import re
import warnings
import email.utils
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai")

def convertir_fecha_correo(fecha_str):
    """Convierte la fecha del correo al formato requerido por BigQuery."""
    try:
        # Parsear la fecha del correo usando email.utils
        timestamp = email.utils.parsedate_to_datetime(fecha_str)
        # Convertir al formato requerido por BigQuery: YYYY-MM-DD HH:MM:SS
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"[LOG] Error al convertir fecha '{fecha_str}': {e}")
        return None

def crear_datos_tarea(correo_id, resultado_json):
    """Crea los datos para insertar una nueva tarea basada en el análisis del correo."""
    fecha_actual = datetime.utcnow().isoformat()
    
    datos_tarea = {
        'CorreoId': correo_id,
        'TipoTarea': resultado_json.get('Clasificacion', 'No especificada'),
        'PrioridadId': resultado_json.get('PrioridadId', 1),  # Extraído por Vertex AI
        'EstimacionDias': None,  # Campo vacío, será editado por el usuario
        'Origen': 'GMAIL',
        'Objetivo': resultado_json.get('HowToFixIt', 'No especificada'),
        'MaterialAdicional': '',  # Campo vacío por ahora
        'EstadoId': 1,  # 1 = "Pending"
        'FechaCreacion': fecha_actual,
        'FechaActualizacion': None  # Campo vacío, se actualizará cuando se modifique la tarea
    }
    
    return datos_tarea

def main(request: Request):
    """Función principal para Cloud Function."""
    print("[LOG] Iniciando procesamiento de correos...")
    print("")
    
    # Validar configuración
    if not validate_and_print_config():
        return {'error': 'Configuración inválida', 'status': 'error'}, 400
    
    # Obtener configuración
    config = get_config()
    
    service = gmail_service_oauth()
    print("[LOG] Servicio de Gmail inicializado.")
    print("")
    correos = listar_correos(service, max_results=20)
    print(f"[LOG] Correos encontrados: {len(correos)}")
    print("")
    resultados = []
    for correo in correos:
        # Obtener metadatos del correo
        asunto = correo.get('subject', '')
        remitente = correo.get('from', '')
        destinatario = correo.get('to', '')
        fecha = correo.get('date', '')
        print(f"[LOG] Asunto detectado: '{asunto}' para correo ID: {correo['id']}")
        print("")
        if not asunto_relevante(asunto):
            print(f"[LOG] Correo ID: {correo['id']} ignorado por asunto irrelevante: {asunto}")
            print("")
            continue
        print(f"[LOG] Procesando correo ID: {correo['id']}")
        print("")
        if correo_ya_procesado(correo['id'], config.bigquery_table):
            print(f"[LOG] Correo ID: {correo['id']} ya fue procesado. Saltando.")
            print("")
            continue
        contenido = obtener_html_correo(service, correo['id'])
        if contenido:
            print("[LOG] Guardando HTML en Cloud Storage...")
            correo_url = guardar_html_en_storage(contenido, correo['id'], config.bucket_name, asunto, remitente, destinatario, fecha)
            print(f"[LOG] HTML subido a: {correo_url}")
            print("[LOG] Contenido extraído, enviando a Gemini...")
            print("")
            resultado_vertex = analizar_texto_vertex(contenido)
            print(f"[LOG] Respuesta de Gemini: {resultado_vertex}")
            print("")
            respuesta_limpia = resultado_vertex.strip()
            if respuesta_limpia.startswith('```'):
                partes = respuesta_limpia.split('```')
                for parte in partes:
                    if '{' in parte and '}' in parte:
                        respuesta_limpia = parte.strip()
                        break
            # Extraer el bloque JSON entre la primera '{' y la última '}'
            start = respuesta_limpia.find('{')
            end = respuesta_limpia.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = respuesta_limpia[start:end+1]
            else:
                json_str = respuesta_limpia  # Por si acaso
            # Solo reemplazar campos vacíos sin comillas por 'No especificada' usando regex
            json_str = re.sub(r':\s*,', ': "No especificada",', json_str)
            # Intentar parsear el JSON de la respuesta
            try:
                resultado_json = json.loads(json_str)
            except Exception as e:
                print(f"[LOG] Error al parsear JSON de Gemini: {e}")
                print(f"[LOG] Texto que se intentó parsear: {json_str}")
                resultado_json = {}
            # Guardar en 'analisis' solo el texto plano generado por Gemini, no el JSON
            # Si la respuesta de Gemini contiene un bloque JSON, extraer el texto antes o después del JSON
            texto_analisis = resultado_vertex.strip()
            # Si hay un bloque markdown, extraer el texto antes del bloque JSON
            if '```' in texto_analisis:
                partes = texto_analisis.split('```')
                # Tomar la parte antes del bloque JSON si existe
                if partes[0].strip():
                    texto_analisis = partes[0].strip()
                # Si no, tomar la parte después del JSON si existe
                elif len(partes) > 2 and partes[2].strip():
                    texto_analisis = partes[2].strip()
                else:
                    texto_analisis = ''
            # Si el texto es solo el JSON, dejarlo vacío
            if texto_analisis.startswith('{') and texto_analisis.endswith('}'):
                texto_analisis = ''
            # Eliminar procesamiento de fecha_envio
            datos = {
                'CorreoId': correo['id'],
                'FechaProcesamiento': datetime.utcnow().isoformat(),
                'Estado': resultado_json.get('Estado', 'No especificada'),
                'CorreoUrl': correo_url,
                'StoreAccess': correo_url
            }
            for campo in CAMPOS_VERTEX:
                # Saltar los campos que solo son para tareas
                if campo in ['PrioridadId', 'EstimacionDias']:
                    continue
                valor = resultado_json.get(campo, 'No especificada')
                # Para NotificationDate, usar fecha del correo si no se pudo extraer
                if campo == 'NotificationDate' and valor == 'No especificada':
                    fecha_convertida = convertir_fecha_correo(fecha)
                    datos[campo] = fecha_convertida if fecha_convertida else None
                # Para ComplianceDeadline, usar None si no hay fecha válida
                elif campo == 'ComplianceDeadline' and valor == 'No especificada':
                    datos[campo] = None
                else:
                    datos[campo] = valor
            insertar_en_bigquery(datos, config.bigquery_table)
            print("[LOG] Resultado insertado en BigQuery.")
            # Insertar en PostgreSQL si no ha sido procesado
            if not correo_ya_procesado_postgresql(datos["CorreoId"]):
                insertar_en_postgresql(datos)
                print("[LOG] Resultado insertado en PostgreSQL.")
                
                # Crear tarea basada en el análisis del correo
                datos_tarea = crear_datos_tarea(correo['id'], resultado_json)
                insertar_tarea_postgresql(datos_tarea)
                print("[LOG] Tarea creada en PostgreSQL.")
                print("")
            else:
                print("[LOG] Correo ya procesado en PostgreSQL.")
                print("")
            print("")
            resultados.append({'id': correo['id'], 'analisis': resultado_vertex})
        else:
            print("[LOG] No se pudo extraer contenido del correo.")
            print("")
    print("[LOG] Procesamiento finalizado.")
    print("")
    return {'resultados': resultados} 