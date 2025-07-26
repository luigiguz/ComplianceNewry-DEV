import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Cargar .env desde múltiples ubicaciones
env_paths = ['.env', 'src/.env', '../.env']
env_loaded = False

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        env_loaded = True
        print(f"✅ Variables de entorno cargadas desde: {env_path}")
        break

if not env_loaded:
    print("⚠️  No se encontró archivo .env. Asegúrate de crear uno con las variables necesarias.")

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
    "ios submission", "android submission", "submission"
]

# Configuración de campos esperados de Vertex AI
CAMPOS_VERTEX = [
    'AppId', 'Version', 'Motivo', 'Clasificacion', 'HowToFixIt', 'PlataformaOrigen',
    'Guideline', 'RejectInformation', 'NotificationDate', 'ComplianceDeadline', 'StoreLink',
    'PrioridadId', 'EstimacionDias'
]

class Config:
    """Clase para manejar la configuración del sistema."""
    
    def __init__(self):
        """Inicializa la configuración usando variables de entorno locales."""
        pass
    
    @property
    def gmail_user(self) -> str:
        """Email del buzón de Gmail a monitorear."""
        return os.getenv('GMAIL_USER', '')
    
    @property
    def gcp_project(self) -> str:
        """ID del proyecto de GCP."""
        return os.getenv('GCP_PROJECT') or os.getenv('GOOGLE_CLOUD_PROJECT', '')
    
    @property
    def vertex_project_id(self) -> str:
        """ID del proyecto para Vertex AI."""
        return os.getenv('VERTEX_PROJECT_ID') or self.gcp_project
    
    @property
    def vertex_location(self) -> str:
        """Región de Vertex AI."""
        return os.getenv('VERTEX_LOCATION', 'us-central1')
    
    @property
    def vertex_endpoint_id(self) -> Optional[str]:
        """ID del endpoint de Vertex AI (opcional)."""
        return os.getenv('VERTEX_ENDPOINT_ID')
    
    @property
    def bigquery_table(self) -> str:
        """Tabla de BigQuery para almacenar resultados."""
        return os.getenv('BIGQUERY_TABLE', 'proyecto.dataset.tabla_compliance')
    
    @property
    def bucket_name(self) -> str:
        """Nombre del bucket de Cloud Storage."""
        return os.getenv('BUCKET_NAME', 'compliance-storage')
    
    @property
    def pg_host(self) -> str:
        """Host de la base de datos PostgreSQL."""
        return os.getenv('PG_HOST', '')
    
    @property
    def pg_port(self) -> int:
        """Puerto de la base de datos PostgreSQL."""
        return int(os.getenv('PG_PORT', '5432'))
    
    @property
    def pg_user(self) -> str:
        """Usuario de la base de datos PostgreSQL."""
        return os.getenv('PG_USER', '')
    
    @property
    def pg_password(self) -> str:
        """Contraseña de la base de datos PostgreSQL."""
        return os.getenv('PG_PASSWORD', '')
    
    @property
    def pg_database(self) -> str:
        """Nombre de la base de datos PostgreSQL."""
        return os.getenv('PG_DATABASE', '')
    
    @property
    def endpoint_url(self) -> Optional[str]:
        """URL de endpoint externo (opcional)."""
        return os.getenv('ENDPOINT_URL')
    
    @property
    def oauth_credentials_path(self) -> str:
        """Ruta a las credenciales OAuth2."""
        return os.getenv('OAUTH_CREDENTIALS', 'credentials_oauth.json')
    
    @property
    def service_credentials_path(self) -> str:
        """Ruta a las credenciales de servicio de GCP."""
        return os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials_service.json')
    
    def validate_config(self) -> List[str]:
        """
        Valida que la configuración esté completa.
        
        Returns:
            Lista de errores encontrados
        """
        errors = []
        
        if not self.gmail_user:
            errors.append("GMAIL_USER no está configurado")
        
        if not self.gcp_project:
            errors.append("GCP_PROJECT no está configurado")
        
        if not self.bigquery_table:
            errors.append("BIGQUERY_TABLE no está configurado")
        
        # Validar configuración de PostgreSQL si se va a usar
        if any([self.pg_host, self.pg_user, self.pg_password, self.pg_database]):
            if not all([self.pg_host, self.pg_user, self.pg_password, self.pg_database]):
                errors.append("Configuración de PostgreSQL incompleta")
        
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
        print("=== RESUMEN DE CONFIGURACIÓN ===")
        print(f"Gmail User: {self.gmail_user}")
        print(f"GCP Project: {self.gcp_project}")
        print(f"Vertex Project ID: {self.vertex_project_id}")
        print(f"Vertex Location: {self.vertex_location}")
        print(f"BigQuery Table: {self.bigquery_table}")
        print(f"Bucket Name: {self.bucket_name}")
        print(f"PostgreSQL Host: {self.pg_host}")
        print(f"PostgreSQL Database: {self.pg_database}")
        print(f"OAuth Credentials: {self.oauth_credentials_path}")
        print(f"Service Credentials: {self.service_credentials_path}")
        print("================================")

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
    config = get_config()
    errors = config.validate_config()
    
    if errors:
        print("❌ Errores de configuración encontrados:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ Configuración válida")
        config.print_config_summary()
        return True 