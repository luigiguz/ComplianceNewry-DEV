# Configuración de Google Secret Manager

Este proyecto ahora usa Google Secret Manager para manejar todas las configuraciones sensibles en lugar de variables de entorno locales.

## Ventajas de usar Secret Manager

- ✅ **Seguridad**: Los secretos están encriptados y gestionados por Google
- ✅ **Escalabilidad**: Funciona en cualquier entorno (local, Cloud Functions, GKE, etc.)
- ✅ **Auditoría**: Logs de acceso y cambios
- ✅ **Versionado**: Control de versiones de secretos
- ✅ **Sin archivos locales**: No más archivos `.env` en el código

## Configuración Inicial

### 1. Habilitar Secret Manager API

```bash
gcloud services enable secretmanager.googleapis.com
```

### 2. Configurar permisos

Asegúrate de que tu cuenta de servicio tenga permisos para acceder a Secret Manager:

```bash
# Para desarrollo local
gcloud auth application-default login

# Para Cloud Functions (automático)
# No se requiere configuración adicional
```

### 3. Migrar variables existentes

Si tienes un archivo `.env`, puedes migrar automáticamente:

```bash
python src/migrate_to_secrets.py
```

### 4. Crear secretos manualmente

Si prefieres crear los secretos manualmente:

```bash
# Secretos requeridos
echo "compliance@weewoo.com" | gcloud secrets create gmail-user --data-file=-
echo "tu-proyecto.tu-dataset.tabla_compliance" | gcloud secrets create bigquery-table --data-file=-
echo "tu-bucket-name" | gcloud secrets create bucket-name --data-file=-

# Secretos opcionales
echo "us-central1" | gcloud secrets create vertex-location --data-file=-
echo "localhost" | gcloud secrets create pg-host --data-file=-
echo "5432" | gcloud secrets create pg-port --data-file=-
echo "tu-usuario" | gcloud secrets create pg-user --data-file=-
echo "tu-password" | gcloud secrets create pg-password --data-file=-
echo "tu-database" | gcloud secrets create pg-database --data-file=-
```

## Nombres de Secretos

| Variable Original | Nombre del Secreto | Requerido | Descripción |
|------------------|-------------------|-----------|-------------|
| `GMAIL_USER` | `gmail-user` | ✅ | Email del buzón de Gmail |
| `BIGQUERY_TABLE` | `bigquery-table` | ✅ | Tabla de BigQuery |
| `BUCKET_NAME` | `bucket-name` | ✅ | Bucket de Cloud Storage |
| `VERTEX_LOCATION` | `vertex-location` | ❌ | Región de Vertex AI |
| `VERTEX_ENDPOINT_ID` | `vertex-endpoint-id` | ❌ | ID del endpoint de Vertex AI |
| `PG_HOST` | `pg-host` | ❌ | Host de PostgreSQL |
| `PG_PORT` | `pg-port` | ❌ | Puerto de PostgreSQL |
| `PG_USER` | `pg-user` | ❌ | Usuario de PostgreSQL |
| `PG_PASSWORD` | `pg-password` | ❌ | Contraseña de PostgreSQL |
| `PG_DATABASE` | `pg-database` | ❌ | Base de datos PostgreSQL |
| `ENDPOINT_URL` | `endpoint-url` | ❌ | URL de endpoint externo |
| `OAUTH_CREDENTIALS` | `oauth-credentials-path` | ❌ | Ruta a credenciales OAuth |
| `GOOGLE_APPLICATION_CREDENTIALS` | `service-credentials-path` | ❌ | Ruta a credenciales de servicio |

## Verificar Configuración

Para verificar que todo esté configurado correctamente:

```bash
python src/test_local.py
```

## Gestión de Secretos

### Listar secretos
```bash
gcloud secrets list
```

### Ver valor de un secreto
```bash
gcloud secrets versions access latest --secret="gmail-user"
```

### Actualizar un secreto
```bash
echo "nuevo-valor" | gcloud secrets versions add gmail-user --data-file=-
```

### Eliminar un secreto
```bash
gcloud secrets delete gmail-user
```

## Troubleshooting

### Error: "No se pudo determinar el ID del proyecto"

Tienes varias opciones para configurar el Project ID:

#### Opción 1: Variable de entorno (Recomendada para desarrollo)
```bash
# Desarrollo local
export GOOGLE_CLOUD_PROJECT="tu-proyecto-id"

# Cloud Run
gcloud run deploy --set-env-vars GOOGLE_CLOUD_PROJECT=tu-proyecto-id
```

#### Opción 2: Secret Manager
```bash
echo "tu-proyecto-id" | gcloud secrets create gcp-project-id --data-file=-
```

#### Opción 3: Metadata (Automático en Cloud Run)
Si estás ejecutando en Cloud Run, el Project ID se detecta automáticamente.

### Error: "Permission denied"

Verifica que tienes permisos:
```bash
gcloud projects get-iam-policy tu-proyecto-id
```

### Error: "Secret not found"

Verifica que el secreto existe:
```bash
gcloud secrets list --filter="name:gmail-user"
```

## Migración desde Variables de Entorno

Si tienes un archivo `.env` existente, el script de migración automática:

1. Lee todas las variables del archivo `.env`
2. Crea los secretos correspondientes en Secret Manager
3. Mantiene los valores existentes
4. Proporciona feedback sobre el proceso

```bash
python src/migrate_to_secrets.py
```

## Seguridad

- Los secretos están encriptados en reposo
- El acceso está controlado por IAM
- Se registran todos los accesos
- Los valores nunca se muestran en logs
- Se pueden rotar automáticamente

## Costos

Secret Manager tiene un costo por:
- Almacenamiento de secretos
- Accesos a secretos
- Operaciones de gestión

Para la mayoría de aplicaciones, el costo es mínimo (< $1/mes). 