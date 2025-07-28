import logging
import os
from google.cloud import logging as cloud_logging
from datetime import datetime

class CloudLogger:
    """Clase para manejar logging en Google Cloud Logging."""
    
    def __init__(self, logger_name="compliance-newry"):
        """Inicializa el logger de Cloud Logging."""
        self.logger_name = logger_name
        self.setup_logger()
    
    def setup_logger(self):
        """Configura el logger para Cloud Logging."""
        try:
            # Configurar cliente de Cloud Logging
            client = cloud_logging.Client()
            
            # Crear logger
            self.logger = client.logger(self.logger_name)
            
            print(f"[LOG] Cloud Logging configurado para: {self.logger_name}")
                
        except Exception as e:
            # Si hay error, lanzar excepción en lugar de fallback
            raise Exception(f"Error configurando Cloud Logging: {e}")
    
    def log(self, message, severity="INFO", **kwargs):
        """
        Registra un mensaje en Cloud Logging.
        
        Args:
            message: Mensaje a registrar
            severity: Nivel de severidad (INFO, WARNING, ERROR, DEBUG)
            **kwargs: Campos adicionales para el log
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Estructura del log
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'severity': severity,
            **kwargs
        }
        
        # Enviar a Cloud Logging
        self.logger.log_struct(log_entry, severity=severity)
    
    def info(self, message, **kwargs):
        """Registra un mensaje de información."""
        self.log(message, severity="INFO", **kwargs)
    
    def warning(self, message, **kwargs):
        """Registra un mensaje de advertencia."""
        self.log(message, severity="WARNING", **kwargs)
    
    def error(self, message, **kwargs):
        """Registra un mensaje de error."""
        self.log(message, severity="ERROR", **kwargs)
    
    def debug(self, message, **kwargs):
        """Registra un mensaje de debug."""
        self.log(message, severity="DEBUG", **kwargs)
    
    def log_execution_start(self, mode, max_results, fecha_desde=None):
        """Registra el inicio de una ejecución."""
        self.info(
            "Iniciando procesamiento de correos",
            execution_mode=mode,
            max_results=max_results,
            fecha_desde=fecha_desde.isoformat() if fecha_desde else None,
            event_type="execution_start"
        )
    
    def log_execution_end(self, mode, correos_procesados, duracion, estado="COMPLETADO"):
        """Registra el fin de una ejecución."""
        self.info(
            "Procesamiento finalizado",
            execution_mode=mode,
            correos_procesados=correos_procesados,
            duracion_segundos=duracion,
            estado=estado,
            event_type="execution_end"
        )
    
    def log_correo_procesado(self, correo_id, asunto, relevante, procesado=False):
        """Registra el procesamiento de un correo."""
        self.info(
            f"Correo procesado: {asunto}",
            correo_id=correo_id,
            asunto=asunto,
            relevante=relevante,
            procesado=procesado,
            event_type="correo_processed"
        )
    
    def log_error(self, error_message, context=None):
        """Registra un error con contexto."""
        self.error(
            f"Error: {error_message}",
            context=context,
            event_type="error"
        )

# Instancia global del logger
_cloud_logger = None

def get_logger():
    """Obtiene la instancia global del logger."""
    global _cloud_logger
    if _cloud_logger is None:
        _cloud_logger = CloudLogger()
    return _cloud_logger 