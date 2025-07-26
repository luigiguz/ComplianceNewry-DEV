import os
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pdfkit
from google.cloud import storage
from config import PALABRAS_CLAVE, get_config
load_dotenv()

def gmail_service():
    """Servicio de Gmail usando Service Account."""
    config = get_config()
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    delegated_credentials = credentials.with_subject(config.gmail_user)
    service = build('gmail', 'v1', credentials=delegated_credentials)
    return service

def gmail_service_oauth():
    """Servicio de Gmail usando OAuth2."""
    import os.path
    import pickle
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    
    config = get_config()
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = None
    
    # Usar la ruta de credenciales desde la configuración
    credentials_path = config.oauth_credentials_path
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    return service

def listar_correos(service, max_results=50):
    fecha = (datetime.utcnow() - timedelta(days=30)).strftime('%Y/%m/%d')
    query = f'after:{fecha}'  # Traer correos de los últimos 30 días
    results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
    mensajes = results.get('messages', [])
    correos = []
    for mensaje in mensajes:
        msg_id = mensaje['id']
        # Obtener los headers del mensaje para extraer el asunto, from, to y date
        msg = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['Subject', 'From', 'To', 'Date']).execute()
        headers = msg.get('payload', {}).get('headers', [])
        subject, from_, to_, date_ = '', '', '', ''
        for header in headers:
            name = header['name'].lower()
            if name == 'subject':
                subject = header['value']
            elif name == 'from':
                from_ = header['value']
            elif name == 'to':
                to_ = header['value']
            elif name == 'date':
                date_ = header['value']
        correos.append({'id': msg_id, 'subject': subject, 'from': from_, 'to': to_, 'date': date_})
    return correos

def obtener_html_correo(service, msg_id):
    mensaje = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    payload = mensaje['payload']
    partes = payload.get('parts', [])
    for parte in partes:
        if parte['mimeType'] == 'text/html':
            data = parte['body']['data']
            html = base64.urlsafe_b64decode(data).decode('utf-8')
            return html
    for parte in partes:
        if parte['mimeType'] == 'text/plain':
            data = parte['body']['data']
            text = base64.urlsafe_b64decode(data).decode('utf-8')
            return text
    return None 

def generar_html_template(contenido_html, asunto, remitente, destinatario, fecha):
    return f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <style>
            body {{
                font-family: Arial, Helvetica, sans-serif;
                margin: 40px;
                font-size: 15px;
                color: #222;
                background: #fafbfc;
            }}
            .header {{
                background: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }}
            .content {{
                background: #fff;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                line-height: 1.6;
            }}
            .metadata {{
                color: #666;
                font-size: 14px;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 1px solid #eee;
            }}
            .metadata strong {{
                color: #333;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📧 Correo de Compliance</h1>
        </div>
        <div class="content">
            <div class="metadata">
                <p><strong>Asunto:</strong> {asunto}</p>
                <p><strong>De:</strong> {remitente}</p>
                <p><strong>Para:</strong> {destinatario}</p>
                <p><strong>Fecha:</strong> {fecha}</p>
            </div>
            <div class="email-content">
                {contenido_html}
            </div>
        </div>
    </body>
    </html>
    """

def guardar_html_en_storage(html_content, correo_id, bucket_name, asunto='', remitente='', destinatario='', fecha=''):
    # Envolver el HTML en un template bonito
    html_template = generar_html_template(html_content, asunto, remitente, destinatario, fecha)
    
    # Subir a Cloud Storage
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob_name = f"emails/{correo_id}.html"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(html_template, content_type='text/html')
    
    return f"gs://{bucket_name}/{blob_name}"

def asunto_relevante(asunto):
    """Verifica si el asunto del correo contiene palabras clave relevantes."""
    asunto_lower = asunto.lower()
    return any(palabra.lower() in asunto_lower for palabra in PALABRAS_CLAVE) 