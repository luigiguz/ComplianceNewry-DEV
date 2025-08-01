import os
from typing import Dict, List, Optional
from google.cloud import secretmanager
from cloud_logging import get_logger

# Configuración de palabras clave para filtrado de correos
PALABRAS_CLAVE = [
    "rejected", "rejection",
    "removed", "unpublished", "taken down",
    "compliance issue", "compliance violation",
    "privacy policy", "policy violation", "privacy violation",
    "metadata issue", "metadata violation",
    "review failed", "app store review", "review outcome",
    "data safety", "data privacy", "data disclosure",
    "permission policy",
    "content violation", "sensitive content",
    "trademark violation", "brand misuse",
    "inactivity", "no recent updates",
    "screenshot policy", "visual asset violation",
    "release failed", "action required", "immediate changes required",
    "ios submission", "android submission", "submission",
    # Nuevas palabras clave para capturar más correos relevantes
    "build issues", "build failed", "uploaded build has one or more issues",
    "stability issues", "trending stability",
    "crash", "crashes", "crashlytics",
    "samsung issue report",
    "failed processing",
    "widget issues", "widget problem",
    "store policy", "store guidelines", "guideline violation",
    "developer account issues",
    "payment issues", "billing issues",
    "performance issues", "performance problem"
]

# Configuración de campos esperados de Vertex AI
CAMPOS_VERTEX = [
    'AppId', 'Version', 'Motivo', 'Clasificacion', 'HowToFixIt', 'PlataformaOrigen',
    'Guideline', 'RejectInformation', 'NotificationDate', 'ComplianceDeadline', 'StoreLink',
    'PrioridadId', 'EstimacionDias'
]

class Config:
    """Clase para manejar la configuración del sistema usando Google Secret Manager."""
    
    def __init__(self):
        """Inicializa la configuración usando Google Secret Manager."""
        self._client = secretmanager.SecretManagerServiceClient()
        self._project_id = self._get_project_id()
        self._cache = {}
        self.logger = get_logger()
    
    def _get_project_id(self) -> str:
        """Obtiene el ID del proyecto de GCP."""
        # 1. Intentar obtener desde variable de entorno (desarrollo local y Cloud Run)
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT')
        if project_id:
            return project_id
        
        # 2. Intentar obtener desde Secret Manager
        try:
            project_id = self._get_secret('gcp-project-id')
            if project_id:
                return project_id
        except:
            pass
        
        # 3. Intentar obtener desde metadata (Cloud Run, Cloud Functions, etc.)
        try:
            import requests
            response = requests.get(
                'http://metadata.google.internal/computeMetadata/v1/project/project-id',
                headers={'Metadata-Flavor': 'Google'},
                timeout=1
            )
            if response.status_code == 200:
                return response.text
        except:
            pass
        
        # 4. Valor por defecto fijo para newry-dev
        return "newry-dev"
    
    def _get_secret(self, secret_name: str) -> str:
        """Obtiene un secreto desde Google Secret Manager."""
        if secret_name in self._cache:
            return self._cache[secret_name]
        
        try:
            name = f"projects/{self._project_id}/secrets/{secret_name}/versions/latest"
            response = self._client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            self._cache[secret_name] = secret_value
            return secret_value
        except Exception as e:
            raise ValueError(f"No se pudo obtener el secreto '{secret_name}': {e}")
    
    @property
    def gmail_user(self) -> str:
        """Email del buzón de Gmail a monitorear."""
        return self._get_secret('gmail-user')
    
    @property
    def gcp_project(self) -> str:
        """ID del proyecto de GCP."""
        return self._project_id
    
    @property
    def vertex_project_id(self) -> str:
        """ID del proyecto para Vertex AI."""
        return self._project_id
    
    @property
    def vertex_location(self) -> str:
        """Región de Vertex AI."""
        try:
            return self._get_secret('vertex-location')
        except:
            return 'us-central1'
    
    @property
    def vertex_endpoint_id(self) -> Optional[str]:
        """ID del endpoint de Vertex AI (opcional)."""
        try:
            return self._get_secret('vertex-endpoint-id')
        except:
            return None
    
    @property
    def bigquery_table(self) -> str:
        """Tabla de BigQuery para almacenar resultados."""
        return self._get_secret('bigquery-table')
    
    @property
    def bucket_name(self) -> str:
        """Nombre del bucket de Cloud Storage."""
        return self._get_secret('bucket-name')
    
    @property
    def pg_host(self) -> str:
        """Host de la base de datos PostgreSQL."""
        return self._get_secret('pg-host')
    
    @property
    def pg_port(self) -> int:
        """Puerto de la base de datos PostgreSQL."""
        try:
            return int(self._get_secret('pg-port'))
        except:
            return 5432
    
    @property
    def pg_user(self) -> str:
        """Usuario de la base de datos PostgreSQL."""
        return self._get_secret('pg-user')
    
    @property
    def pg_password(self) -> str:
        """Contraseña de la base de datos PostgreSQL."""
        return self._get_secret('pg-password')
    
    @property
    def pg_database(self) -> str:
        """Nombre de la base de datos PostgreSQL."""
        return self._get_secret('pg-database')
    
    @property
    def endpoint_url(self) -> Optional[str]:
        """URL de endpoint externo (opcional)."""
        try:
            return self._get_secret('endpoint-url')
        except:
            return None
    
    @property
    def oauth_credentials_path(self) -> str:
        """Ruta a las credenciales OAuth2."""
        try:
            return self._get_secret('oauth-credentials-path')
        except:
            return 'credentials_oauth.json'
    
    @property
    def service_credentials_path(self) -> str:
        """Ruta a las credenciales de servicio de GCP."""
        try:
            return self._get_secret('service-credentials-path')
        except:
            return 'credentials_service.json'
    
    def validate_config(self) -> List[str]:
        """
        Valida que la configuración esté completa.
        
        Returns:
            Lista de errores encontrados
        """
        errors = []
        
        # Verificar secretos requeridos
        required_secrets = [
            'gmail-user',
            'bigquery-table',
            'bucket-name'
        ]
        
        for secret in required_secrets:
            try:
                self._get_secret(secret)
            except Exception as e:
                errors.append(f"Secreto '{secret}' no encontrado: {e}")
        
        # Validar configuración de PostgreSQL si se va a usar
        pg_secrets = ['pg-host', 'pg-user', 'pg-password', 'pg-database']
        pg_configured = True
        
        for secret in pg_secrets:
            try:
                self._get_secret(secret)
            except:
                pg_configured = False
                break
        
        if pg_configured:
            self.logger.info("Configuración de PostgreSQL detectada")
        else:
            self.logger.warning("Configuración de PostgreSQL no encontrada (opcional)")
        
        return errors
    
    def get_postgres_config(self) -> Dict[str, str]:
        """Obtiene la configuración de PostgreSQL como diccionario."""
        return {
            'host': self.pg_host,
            'port': str(self.pg_port),
            'user': self.pg_user,
            'password': self.pg_password,
            'database': self.pg_database
        }
    
    def print_config_summary(self):
        """Imprime un resumen de la configuración actual."""
        self.logger.info("=== RESUMEN DE CONFIGURACIÓN (Secret Manager) ===")
        self.logger.info(f"Gmail User: {self.gmail_user}")
        self.logger.info(f"GCP Project: {self.gcp_project}")
        self.logger.info(f"Vertex Project ID: {self.vertex_project_id}")
        self.logger.info(f"Vertex Location: {self.vertex_location}")
        self.logger.info(f"BigQuery Table: {self.bigquery_table}")
        self.logger.info(f"Bucket Name: {self.bucket_name}")
        self.logger.info(f"PostgreSQL Host: {self.pg_host}")
        self.logger.info(f"PostgreSQL Database: {self.pg_database}")
        self.logger.info(f"OAuth Credentials: {self.oauth_credentials_path}")
        self.logger.info(f"Service Credentials: {self.service_credentials_path}")
        self.logger.info("================================================")

# Instancia global de configuración
_config = None

def get_config() -> Config:
    """Obtiene la instancia global de configuración."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def validate_and_print_config():
    """Valida la configuración e imprime errores si los hay."""
    try:
        config = get_config()
        errors = config.validate_config()
        
        if errors:
            config.logger.error("Errores de configuración encontrados:")
            for error in errors:
                config.logger.error(f"  - {error}")
            return False
        else:
            config.logger.info("Configuración válida")
            config.print_config_summary()
            return True
    except Exception as e:
        logger = get_logger()
        logger.error(f"Error al inicializar configuración: {e}")
        return False 