#!/usr/bin/env python3
"""
Script para probar Cloud Logging
"""

from cloud_logging import get_logger
import time

def test_cloud_logging():
    """Prueba el sistema de Cloud Logging."""
    print("Iniciando prueba de Cloud Logging...")
    
    try:
        # Obtener logger
        logger = get_logger()
        print("✅ Logger obtenido correctamente")
        
        # Probar diferentes tipos de logs
        logger.info("Prueba de log de información", test_type="info")
        print("✅ Log de información enviado")
        
        logger.warning("Prueba de log de advertencia", test_type="warning")
        print("✅ Log de advertencia enviado")
        
        logger.error("Prueba de log de error", test_type="error")
        print("✅ Log de error enviado")
        
        # Probar logs estructurados
        logger.log_execution_start(mode="test", max_results=10)
        print("✅ Log de inicio de ejecución enviado")
        
        time.sleep(2)  # Simular procesamiento
        
        logger.log_execution_end(mode="test", correos_procesados=5, duracion=2.0)
        print("✅ Log de fin de ejecución enviado")
        
        # Probar log de correo
        logger.log_correo_procesado(
            correo_id="test_123",
            asunto="Test Subject",
            relevante=True,
            procesado=True
        )
        print("✅ Log de correo procesado enviado")
        
        print("\n🎉 ¡Todas las pruebas de Cloud Logging completadas!")
        print("Revisa los logs en Google Cloud Console:")
        print("https://console.cloud.google.com/logs/query?project=newry-dev")
        print("Filtro sugerido: resource.type=\"cloud_run_revision\" OR resource.type=\"global\"")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        print("Verifica que:")
        print("1. Tienes credenciales configuradas: gcloud auth application-default login")
        print("2. La variable GOOGLE_CLOUD_PROJECT está configurada")
        print("3. Tienes permisos para Cloud Logging")

if __name__ == "__main__":
    test_cloud_logging() 