import os
from vertexai.generative_models import GenerativeModel
from vertexai import init
from config import get_config

def analizar_texto_vertex(texto):
    """Analiza el texto usando Gemini Pro en Vertex AI Generative AI para extraer entidades, clasificar y sugerir solución."""
    # Obtener configuración
    config = get_config()
    
    # Prints de depuración
    print("PROJECT_ID:", config.vertex_project_id)
    print("LOCATION:", config.vertex_location)
    
    # Inicializa Vertex AI (esto se puede llamar varias veces sin problema)
    init(project=config.vertex_project_id, location=config.vertex_location)
    model = GenerativeModel("gemini-2.5-pro")
    prompt = f'''
Analiza el siguiente mensaje y extrae la siguiente información en formato JSON. Si algún dato no está presente en el mensaje, coloca exactamente "No especificada" como valor. Para las fechas (NotificationDate y ComplianceDeadline), usa el formato exacto YYYY-MM-DD HH:MM:SS:
{{
  "AppId": string,  # Identificador único de la app afectada por el incumplimiento. Puede coincidir con el nombre de la app o el ID interno.
  "Version": string,  # Versión específica de la app mencionada en el mensaje de rechazo.
  "Motivo": string,  # Texto general del motivo del rechazo, resumido.
  "Clasificacion": string,  # Categoría del problema de compliance: Ads, Metadata, Privacy, Screenshots, etc.
  "HowToFixIt": string,  # Sugerencia clara, breve y accionable para resolver el problema, dirigida a un desarrollador. Evita frases genéricas. Explica exactamente qué debe hacer el desarrollador, incluyendo pasos técnicos, archivos o configuraciones a modificar, y ejemplos de código si es posible. Sé concreto y directo.
  "PlataformaOrigen": string,  # Plataforma a la que pertenece la app: iOS o Android.
  "Guideline": string,  # Política o norma específica que fue incumplida, extraída del mensaje.
  "RejectInformation": string,  # Texto literal del mensaje de rechazo emitido por Apple o Google.
  "NotificationDate": string,  # Fecha y hora en que fue recibido el correo o la notificación de la store, en formato YYYY-MM-DD HH:MM:SS.
  "ComplianceDeadline": string,  # Fecha límite establecida por la store para corregir el incumplimiento, en formato YYYY-MM-DD HH:MM:SS.
  "StoreLink": string,  # Enlace directo a la app en Google Play o App Store.
  "PrioridadId": number,  # Nivel de prioridad de la tarea. RESPONDE SOLO CON EL ID NUMÉRICO: 1=A+ (Crítica), 2=A (Alta), 3=B (Media), 4=C (Baja). Basa la prioridad en la severidad del incumplimiento, el impacto en el negocio y la urgencia de la corrección.
  "EstimacionDias": number  # Número estimado de días para completar la tarea de corrección. Considera la complejidad técnica, recursos necesarios y experiencia del equipo.
}}

Mensaje:
"""
{texto}
"""
Devuelve solo el JSON.
'''
    response = model.generate_content(prompt)
    return response.text 