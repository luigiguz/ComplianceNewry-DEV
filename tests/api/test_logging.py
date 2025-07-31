#!/usr/bin/env python3
"""
Script de prueba para el sistema de logging dual (terminal + Cloud Logging)
"""

import os
import sys

# Configurar el proyecto GCP
os.environ['GOOGLE_CLOUD_PROJECT'] = 'newry-dev'

# Agregar src al path
sys.path.append('src')

from cloud_logging import get_logger

def test_logging():
    """Prueba todos los niveles de logging."""
    logger = get_logger()
    
    print("=== PRUEBA DE LOGGING DUAL ===")
    print("Los siguientes mensajes aparecerán tanto en terminal como en Cloud Logging:")
    print()
    
    # Probar diferentes niveles
    logger.debug("Este es un mensaje de DEBUG")
    logger.info("Este es un mensaje de INFO")
    logger.warning("Este es un mensaje de WARNING")
    logger.error("Este es un mensaje de ERROR")
    
    # Probar con campos adicionales
    logger.info("Procesando correo", correo_id="12345", asunto="Test Subject")
    logger.warning("Correo no relevante", correo_id="67890", relevante=False)
    
    # Probar funciones específicas
    logger.log_execution_start(mode="test", max_results=10)
    logger.log_correo_procesado("test-123", "Test Email", True, True)
    logger.log_execution_end("test", 1, 5.2)
    
    print()
    print("=== PRUEBA COMPLETADA ===")
    print("Revisa Cloud Logging para ver los mensajes estructurados")

if __name__ == "__main__":
    test_logging() 