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