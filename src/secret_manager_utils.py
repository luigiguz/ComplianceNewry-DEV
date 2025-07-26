import os
import json
from google.cloud import secretmanager
from typing import Optional, Dict, Any

class SecretManagerClient:
    """Cliente para manejar secretos en Google Cloud Secret Manager."""
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Inicializa el cliente de Secret Manager.
        
        Args:
            project_id: ID del proyecto de GCP. Si no se proporciona, 
                       se usa la variable de entorno GOOGLE_CLOUD_PROJECT.
        """
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        if not self.project_id:
            raise ValueError("Se requiere project_id o variable GOOGLE_CLOUD_PROJECT")
        
        self.client = secretmanager.SecretManagerServiceClient()
    
    def get_secret(self, secret_id: str, version_id: str = "latest") -> str:
        """
        Obtiene un secreto específico.
        
        Args:
            secret_id: ID del secreto (sin el prefijo del proyecto)
            version_id: Versión del secreto (default: "latest")
            
        Returns:
            El valor del secreto como string
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
        
        try:
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"Error al obtener secreto {secret_id}: {e}")
            raise
    
    def get_secret_json(self, secret_id: str, version_id: str = "latest") -> Dict[str, Any]:
        """
        Obtiene un secreto y lo parsea como JSON.
        
        Args:
            secret_id: ID del secreto
            version_id: Versión del secreto
            
        Returns:
            El secreto parseado como diccionario
        """
        secret_value = self.get_secret(secret_id, version_id)
        try:
            return json.loads(secret_value)
        except json.JSONDecodeError as e:
            print(f"Error al parsear JSON del secreto {secret_id}: {e}")
            raise
    
    def create_secret(self, secret_id: str, secret_value: str) -> str:
        """
        Crea un nuevo secreto.
        
        Args:
            secret_id: ID del secreto
            secret_value: Valor del secreto
            
        Returns:
            Nombre del secreto creado
        """
        parent = f"projects/{self.project_id}"
        
        try:
            # Crear el secreto
            secret = {"replication": {"automatic": {}}}
            secret_name = self.client.create_secret(
                request={"parent": parent, "secret_id": secret_id, "secret": secret}
            )
            
            # Agregar la versión del secreto
            payload = secret_value.encode("UTF-8")
            self.client.add_secret_version(
                request={"parent": secret_name.name, "payload": {"data": payload}}
            )
            
            return secret_name.name
        except Exception as e:
            print(f"Error al crear secreto {secret_id}: {e}")
            raise
    
    def update_secret(self, secret_id: str, secret_value: str) -> str:
        """
        Actualiza un secreto existente agregando una nueva versión.
        
        Args:
            secret_id: ID del secreto
            secret_value: Nuevo valor del secreto
            
        Returns:
            Nombre de la nueva versión del secreto
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}"
        payload = secret_value.encode("UTF-8")
        
        try:
            response = self.client.add_secret_version(
                request={"parent": name, "payload": {"data": payload}}
            )
            return response.name
        except Exception as e:
            print(f"Error al actualizar secreto {secret_id}: {e}")
            raise

# Instancia global del cliente
_secret_client = None

def get_secret_client() -> SecretManagerClient:
    """Obtiene la instancia global del cliente de Secret Manager."""
    global _secret_client
    if _secret_client is None:
        _secret_client = SecretManagerClient()
    return _secret_client

def get_config_from_secrets() -> Dict[str, str]:
    """
    Obtiene toda la configuración desde Secret Manager.
    
    Returns:
        Diccionario con todas las variables de configuración
    """
    client = get_secret_client()
    
    # Mapeo de nombres de secretos a variables de entorno
    secret_mapping = {
        'gmail-user': 'GMAIL_USER',
        'gmail-oauth-credentials': 'OAUTH_CREDENTIALS',
        'gcp-project': 'GCP_PROJECT',
        'vertex-project-id': 'VERTEX_PROJECT_ID',
        'vertex-location': 'VERTEX_LOCATION',
        'vertex-endpoint-id': 'VERTEX_ENDPOINT_ID',
        'bigquery-table': 'BIGQUERY_TABLE',
        'bucket-name': 'BUCKET_NAME',
        'pg-host': 'PG_HOST',
        'pg-port': 'PG_PORT',
        'pg-user': 'PG_USER',
        'pg-password': 'PG_PASSWORD',
        'pg-database': 'PG_DATABASE',
        'endpoint-url': 'ENDPOINT_URL'
    }
    
    config = {}
    
    for secret_id, env_var in secret_mapping.items():
        try:
            # Para credenciales JSON, obtener como JSON
            if secret_id in ['gmail-oauth-credentials']:
                secret_value = client.get_secret_json(secret_id)
                config[env_var] = json.dumps(secret_value)
            else:
                config[env_var] = client.get_secret(secret_id)
        except Exception as e:
            print(f"Advertencia: No se pudo obtener el secreto {secret_id}: {e}")
            # Usar valor de entorno como fallback
            config[env_var] = os.getenv(env_var)
    
    return config

def setup_environment_from_secrets():
    """
    Configura las variables de entorno desde Secret Manager.
    Si un secreto no existe, usa la variable de entorno como fallback.
    """
    config = get_config_from_secrets()
    
    for env_var, value in config.items():
        if value is not None:
            os.environ[env_var] = value
            print(f"Configurada variable {env_var} desde Secret Manager")
        else:
            print(f"Advertencia: Variable {env_var} no encontrada en Secret Manager ni en entorno")

# Función de conveniencia para obtener un secreto específico
def get_secret(secret_id: str) -> str:
    """Obtiene un secreto específico usando la instancia global."""
    return get_secret_client().get_secret(secret_id)

def get_secret_json(secret_id: str) -> Dict[str, Any]:
    """Obtiene un secreto JSON específico usando la instancia global."""
    return get_secret_client().get_secret_json(secret_id) 