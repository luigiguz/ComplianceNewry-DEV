import os.path
import json
import tempfile
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle
from config import get_config

# Configurar el proyecto GCP directamente en el código
os.environ['GOOGLE_CLOUD_PROJECT'] = 'newry-dev'

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Obtiene el servicio de Gmail usando credenciales desde Secret Manager."""
    creds = None
    
    # El token se guarda aquí después del primer login
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Si no hay token o está expirado, pide login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Obtener credenciales desde Secret Manager
            config = get_config()
            try:
                # Intentar obtener las credenciales OAuth desde Secret Manager
                oauth_credentials_json = config._get_secret('oauth-credentials')
                
                # Crear un archivo temporal con las credenciales
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                    temp_file.write(oauth_credentials_json)
                    temp_credentials_path = temp_file.name
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        temp_credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                finally:
                    # Limpiar el archivo temporal
                    os.unlink(temp_credentials_path)
                    
            except Exception as e:
                # Fallback: intentar usar archivo local si existe
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    raise ValueError(f"No se pudieron obtener las credenciales OAuth desde Secret Manager ni desde archivo local: {e}")
        
        # Guarda el token para la próxima vez
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    service = build('gmail', 'v1', credentials=creds)
    return service

# Ejemplo de uso:
if __name__ == '__main__':
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', maxResults=5).execute()
        print("✅ Conexión exitosa a Gmail")
        print(f"Encontrados {len(results.get('messages', []))} mensajes")
    except Exception as e:
        print(f"❌ Error conectando a Gmail: {e}")
        print("\nPosibles soluciones:")
        print("1. Asegúrate de que el secreto 'oauth-credentials' existe en Secret Manager")
        print("2. Verifica que tienes permisos para acceder a Secret Manager")
        print("3. Ejecuta: gcloud auth application-default login")
        print("4. O coloca un archivo 'credentials.json' en el directorio actual")