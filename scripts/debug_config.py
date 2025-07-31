#!/usr/bin/env python3
"""
Script para diagnosticar problemas de configuración
"""

import os
import sys

# Configurar el proyecto GCP
os.environ['GOOGLE_CLOUD_PROJECT'] = 'newry-dev'

# Agregar src al path
sys.path.append('src')

try:
    from config import get_config, validate_and_print_config
    
    print("=== DIAGNÓSTICO DE CONFIGURACIÓN ===")
    print(f"Proyecto GCP: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'No configurado')}")
    
    # Intentar obtener configuración
    config = get_config()
    print("✅ Configuración inicializada")
    
    # Validar configuración
    errors = config.validate_config()
    
    if errors:
        print("\n❌ Errores encontrados:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ Configuración válida")
        config.print_config_summary()
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 