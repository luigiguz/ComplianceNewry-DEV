# Checklist de Despliegue - Compliance Newry API

## ✅ Pre-Despliegue

### 1. Configuración de GCP
- [ ] Proyecto configurado: `newry-dev`
- [ ] APIs habilitadas:
  - [ ] Cloud Run API
  - [ ] Secret Manager API
  - [ ] Cloud Logging API
  - [ ] Gmail API
  - [ ] Vertex AI API
  - [ ] BigQuery API
  - [ ] Cloud Storage API

### 2. Secret Manager
- [ ] `gmail-user` = `compliance@weewoo.com`
- [ ] `bigquery-table` = `newry-dev.correos_analisis.ComplianceIssues`
- [ ] `bucket-name` = `correos-procesados-newry`
- [ ] `pg-host` = `35.192.74.225`
- [ ] `pg-user` = [tu usuario PostgreSQL]
- [ ] `pg-password` = [tu contraseña PostgreSQL]
- [ ] `pg-database` = `newry_compliance`
- [ ] `vertex-location` = `us-central1`
- [ ] `oauth-credentials-path` = `credentials_oauth.json`
- [ ] `service-credentials-path` = `credentials_service.json`

### 3. Credenciales OAuth
- [ ] Archivo `credentials_oauth.json` subido a Secret Manager
- [ ] Email `compliance@weewoo.com` agregado como usuario de prueba en Google Cloud Console
- [ ] Permisos de Gmail API configurados

### 4. Base de Datos
- [ ] Tabla `ComplianceEjecuciones` creada en PostgreSQL
- [ ] Conexión a PostgreSQL funcionando
- [ ] Índices creados para optimización

### 5. Archivos de Código
- [ ] `Dockerfile` creado
- [ ] `.dockerignore` configurado
- [ ] `requirements.txt` actualizado
- [ ] Todos los logs usando Cloud Logging

## 🚀 Despliegue

### Comando de Despliegue
```bash
gcloud run deploy compliance-processor \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=newry-dev \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900 \
  --max-instances 10
```



## ✅ Post-Despliegue

### 1. Verificación de URLs
- [ ] Health Check: `https://compliance-processor-xxxxx-uc.a.run.app/`
- [ ] Swagger UI: `https://compliance-processor-xxxxx-uc.a.run.app/swagger`
- [ ] API Endpoint: `https://compliance-processor-xxxxx-uc.a.run.app/api/v1/process-emails`

### 2. Pruebas de Funcionalidad
- [ ] Health check responde correctamente
- [ ] Swagger UI carga sin errores
- [ ] API procesa correos correctamente
- [ ] Logs aparecen en Cloud Logging

### 3. Monitoreo
- [ ] Cloud Logging configurado con filtro:
  ```
  resource.type="cloud_run_revision" AND logName="projects/newry-dev/logs/compliance-newry"
  ```
- [ ] Alertas configuradas para errores
- [ ] Métricas de Cloud Run monitoreadas

## 🔧 Troubleshooting

### Errores Comunes
1. **Error de permisos:** Verificar IAM roles
2. **Error de secretos:** Verificar que todos los secretos existan
3. **Error de OAuth:** Verificar credenciales y usuarios de prueba
4. **Error de base de datos:** Verificar conexión y permisos
5. **Timeout:** Aumentar timeout en Cloud Run

### Logs Útiles
```bash
# Ver logs en tiempo real
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=compliance-processor"

# Ver logs específicos de la aplicación
gcloud logging tail "logName=projects/newry-dev/logs/compliance-newry"
``` 