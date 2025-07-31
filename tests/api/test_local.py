import sys
import os

# Configurar el proyecto GCP
os.environ['GOOGLE_CLOUD_PROJECT'] = 'newry-dev'

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from main import main
from flask import Request
from werkzeug.test import EnvironBuilder

# Simula una petición POST vacía
builder = EnvironBuilder(method='POST', data='{}', content_type='application/json')
env = builder.get_environ()
request = Request(env)

# Llama a la función principal
response = main(request)
print(response)