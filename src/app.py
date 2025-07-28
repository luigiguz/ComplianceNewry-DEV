import os
import sys

# Agregar logging básico para debugging
print("Iniciando aplicación...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

try:
    from flask import Flask, request, jsonify
    print("Flask importado correctamente")
except Exception as e:
    print(f"Error importando Flask: {e}")
    raise

try:
    from flask_cors import CORS
    print("Flask-CORS importado correctamente")
except Exception as e:
    print(f"Error importando Flask-CORS: {e}")
    raise

try:
    from flasgger import Swagger, swag_from
    print("Flasgger importado correctamente")
except Exception as e:
    print(f"Error importando Flasgger: {e}")
    raise

from datetime import datetime

# Importar módulos del proyecto
try:
    from main import main as process_emails
    print("Módulo main importado correctamente")
except Exception as e:
    print(f"Error importando main: {e}")
    raise

try:
    from cloud_logging import get_logger
    print("Módulo cloud_logging importado correctamente")
except Exception as e:
    print(f"Error importando cloud_logging: {e}")
    raise

# Configurar Flask
app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas

# Configurar Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Compliance Newry API",
        "description": "API para procesamiento automático de correos de compliance usando Google Cloud Platform, Vertex AI y PostgreSQL.",
        "contact": {
            "name": "Luis Guzmán"
        },
        "version": "1.0.0"
    },
    "basePath": "/",
    "schemes": [
        "https"
    ],
    "consumes": [
        "application/json"
    ],
    "produces": [
        "application/json"
    ],
    "tags": [
        {
            "name": "Procesamiento",
            "description": "Endpoint para procesamiento de correos"
        }
    ],
    "swagger_ui_bundle_js": "//unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js",
    "swagger_ui_standalone_preset_js": "//unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js",
    "jquery_js": "//unpkg.com/jquery@2.2.4/dist/jquery.min.js",
    "swagger_ui_css": "//unpkg.com/swagger-ui-dist@3/swagger-ui.css",
    "favicon": "//unpkg.com/swagger-ui-dist@3/favicon-32x32.png",
    "swagger_ui_js": "//unpkg.com/swagger-ui-dist@3/swagger-ui.js"
}

swagger = Swagger(app, config=swagger_config, template=swagger_template, decorators=[lambda f: f])

# Obtener logger
logger = get_logger()

@app.route('/')
def health_check():
    """Endpoint de verificación de salud de la API."""
    return jsonify({
        'status': 'success',
        'message': 'Compliance Newry API funcionando correctamente',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/v1/process-emails', methods=['POST'])
@swag_from({
    'tags': ['Procesamiento'],
    'summary': 'Procesar correos de compliance',
    'description': 'Inicia el procesamiento automático de correos de compliance. Detecta automáticamente si es carga inicial o procesamiento incremental.',
    'responses': {
        200: {
            'description': 'Procesamiento completado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'message': {'type': 'string'},
                    'modo': {'type': 'string'},
                    'correos_procesados': {'type': 'integer'},
                    'duracion_segundos': {'type': 'number'},
                    'resultados': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string'},
                                'analisis': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Error en la configuración o procesamiento',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'status': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Error interno del servidor',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'status': {'type': 'string'}
                }
            }
        }
    }
})
def process_emails_endpoint():
    """Endpoint para procesar correos de compliance."""
    try:
        logger.info("Iniciando procesamiento de correos via API")
        
        # Crear request simulado para la función main
        class MockRequest:
            def get_json(self):
                return {}
        
        # Ejecutar procesamiento
        result = process_emails(MockRequest())
        
        logger.info("Procesamiento completado via API", 
                   modo=result.get('modo'),
                   correos_procesados=result.get('correos_procesados'))
        
        return jsonify({
            'status': 'success',
            'message': 'Procesamiento completado exitosamente',
            **result
        }), 200
        
    except Exception as e:
        logger.error(f"Error en procesamiento via API: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    try:
        # Configurar puerto desde variable de entorno o usar 5000 por defecto
        port = int(os.environ.get('PORT', 5000))
        
        logger.info(f"Iniciando API en puerto {port}")
        logger.info(f"GOOGLE_CLOUD_PROJECT: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'No configurado')}")
        
        # Ejecutar en modo debug solo en desarrollo
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        logger.info("Iniciando servidor Flask...")
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug
        )
    except Exception as e:
        logger.error(f"Error iniciando la aplicación: {str(e)}")
        raise 