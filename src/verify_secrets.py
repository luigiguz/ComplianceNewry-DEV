#!/usr/bin/env python3
"""
Script para verificar que todos los secretos necesarios estén en Secret Manager
"""

from google.cloud import secretmanager
import os

def verify_secrets():
    """Verifica que todos los secretos necesarios estén en Secret Manager."""
    
    # Obtener proyecto ID
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'newry-dev')
    
    # Lista de secretos requeridos
    required_secrets = [
        'gmail-user',
        'bigquery-table',
        'bucket-name',
        'pg-host',
        'pg-user',
        'pg-password',
        'pg-database',
        'vertex-location',
        'oauth-credentials',
        'service-credentials'
    ]
    
    print(f"Verificando secretos en proyecto: {project_id}")
    print("=" * 50)
    
    client = secretmanager.SecretManagerServiceClient()
    
    missing_secrets = []
    existing_secrets = []
    
    for secret_name in required_secrets:
        try:
            secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": secret_path})
            print(f"✅ {secret_name}: OK")
            existing_secrets.append(secret_name)
        except Exception as e:
            print(f"❌ {secret_name}: FALTANTE - {str(e)}")
            missing_secrets.append(secret_name)
    
    print("\n" + "=" * 50)
    print("RESUMEN:")
    print(f"Secretos existentes: {len(existing_secrets)}/{len(required_secrets)}")
    print(f"Secretos faltantes: {len(missing_secrets)}")
    
    if missing_secrets:
        print("\nSecretos que necesitas crear:")
        for secret in missing_secrets:
            print(f"  - {secret}")
        
        print("\nComandos para crear los secretos:")
        for secret in missing_secrets:
            if secret == 'oauth-credentials':
                print(f"# Subir archivo credentials_oauth.json:")
                print(f"gcloud secrets create {secret} --data-file=credentials_oauth.json")
            elif secret == 'service-credentials':
                print(f"# Subir archivo credentials_service.json:")
                print(f"gcloud secrets create {secret} --data-file=credentials_service.json")
            else:
                print(f"gcloud secrets create {secret} --data-file=-")
                print(f"echo 'valor_del_secreto' | gcloud secrets versions add {secret} --data-file=-")
    else:
        print("🎉 ¡Todos los secretos están configurados correctamente!")
    
    return len(missing_secrets) == 0

if __name__ == "__main__":
    verify_secrets() 