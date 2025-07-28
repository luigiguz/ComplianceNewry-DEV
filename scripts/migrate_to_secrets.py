#!/usr/bin/env python3
"""
Script para migrar variables de entorno locales a Google Secret Manager.
"""

import os
import json
from google.cloud import secretmanager
from dotenv import load_dotenv

def get_project_id():
    """Obtiene el ID del proyecto de GCP."""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT')
    if not project_id:
        raise ValueError("No se pudo determinar el ID del proyecto. Configura GOOGLE_CLOUD_PROJECT o GCP_PROJECT")
    return project_id

def create_secret(client, project_id, secret_id, secret_value):
    """Crea un secreto en Secret Manager."""
    parent = f"projects/{project_id}"
    
    # Crear el secreto
    try:
        secret = client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}}
            }
        )
        print(f"✅ Secreto '{secret_id}' creado")
    except Exception as e:
        if "already exists" in str(e):
            print(f"⚠️  Secreto '{secret_id}' ya existe")
        else:
            print(f"❌ Error creando secreto '{secret_id}': {e}")
            return False
    
    # Agregar la versión del secreto
    try:
        client.add_secret_version(
            request={
                "parent": secret.name,
                "payload": {"data": secret_value.encode("UTF-8")}
            }
        )
        print(f"✅ Versión del secreto '{secret_id}' agregada")
        return True
    except Exception as e:
        print(f"❌ Error agregando versión del secreto '{secret_id}': {e}")
        return False

def migrate_env_to_secrets():
    """Migra las variables de entorno a Secret Manager."""
    print("=== MIGRACIÓN A GOOGLE SECRET MANAGER ===")
    print("")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Obtener proyecto ID
    try:
        project_id = get_project_id()
        print(f"Proyecto GCP: {project_id}")
        print("")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Crear cliente de Secret Manager
    try:
        client = secretmanager.SecretManagerServiceClient()
        print("✅ Cliente de Secret Manager inicializado")
        print("")
    except Exception as e:
        print(f"❌ Error inicializando Secret Manager: {e}")
        return False
    
    # Mapeo de variables de entorno a nombres de secretos
    env_to_secrets = {
        'GMAIL_USER': 'gmail-user',
        'BIGQUERY_TABLE': 'bigquery-table',
        'BUCKET_NAME': 'bucket-name',
        'VERTEX_LOCATION': 'vertex-location',
        'VERTEX_ENDPOINT_ID': 'vertex-endpoint-id',
        'PG_HOST': 'pg-host',
        'PG_PORT': 'pg-port',
        'PG_USER': 'pg-user',
        'PG_PASSWORD': 'pg-password',
        'PG_DATABASE': 'pg-database',
        'ENDPOINT_URL': 'endpoint-url',
        'OAUTH_CREDENTIALS': 'oauth-credentials-path',
        'GOOGLE_APPLICATION_CREDENTIALS': 'service-credentials-path'
    }
    
    # Secretos requeridos (deben existir)
    required_secrets = ['GMAIL_USER', 'BIGQUERY_TABLE', 'BUCKET_NAME']
    
    print("=== SECRETOS REQUERIDOS ===")
    for env_var in required_secrets:
        secret_id = env_to_secrets[env_var]
        secret_value = os.getenv(env_var)
        
        if not secret_value:
            print(f"❌ {env_var} no está configurado")
            continue
        
        print(f"Migrando {env_var} -> {secret_id}")
        if create_secret(client, project_id, secret_id, secret_value):
            print(f"  Valor: {secret_value[:20]}..." if len(secret_value) > 20 else f"  Valor: {secret_value}")
        print("")
    
    print("=== SECRETOS OPCIONALES ===")
    for env_var, secret_id in env_to_secrets.items():
        if env_var in required_secrets:
            continue
        
        secret_value = os.getenv(env_var)
        if not secret_value:
            print(f"⚠️  {env_var} no configurado (opcional)")
            continue
        
        print(f"Migrando {env_var} -> {secret_id}")
        if create_secret(client, project_id, secret_id, secret_value):
            print(f"  Valor: {secret_value[:20]}..." if len(secret_value) > 20 else f"  Valor: {secret_value}")
        print("")
    
    print("=== MIGRACIÓN COMPLETADA ===")
    print("")
    print("✅ Los secretos han sido creados en Google Secret Manager")
    print("")
    print("Próximos pasos:")
    print("1. Verifica que todos los secretos se crearon correctamente")
    print("2. Asegúrate de que tu aplicación tenga permisos para acceder a Secret Manager")
    print("3. Prueba la nueva configuración ejecutando: python src/test_local.py")
    print("")
    print("Para verificar los secretos creados:")
    print(f"gcloud secrets list --project={project_id}")
    
    return True

if __name__ == "__main__":
    migrate_env_to_secrets() 