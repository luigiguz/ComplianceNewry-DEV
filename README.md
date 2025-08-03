# Compliance Newry - Sistema de Procesamiento de Correos

Sistema automatizado para procesar correos de compliance usando Google Cloud Platform, Vertex AI y PostgreSQL.

## Características

- ✅ **API REST** con documentación Swagger/OpenAPI
- ✅ **Procesamiento automático** de correos de compliance
- ✅ **Análisis con Vertex AI** (Gemini) para extracción de información
- ✅ **Almacenamiento en BigQuery** y PostgreSQL
- ✅ **Control de ejecuciones** con procesamiento incremental
- ✅ **Configuración segura** con Google Secret Manager
- ✅ **Logging centralizado** con Google Cloud Logging
- ✅ **Filtrado inteligente** de correos relevantes
- ✅ **CORS habilitado** para integración frontend

## Configuración

### Variables de Entorno Requeridas

```bash
export GOOGLE_CLOUD_PROJECT="newry-dev"
```

### Secret Manager

El sistema usa Google Secret Manager para todas las configuraciones sensibles:

- `gmail-user`: Email del buzón de Gmail
- `bigquery-table`: Tabla de BigQuery
- `bucket-name`: Bucket de Cloud Storage
- `pg-host`, `pg-user`, `pg-password`, `pg-database`: Configuración PostgreSQL

## Uso

### Desarrollo Local

#### Opción 1: API REST (Recomendado)

```bash
# Configurar proyecto
export GOOGLE_CLOUD_PROJECT="newry-dev"

# Iniciar la API
python src/app.py

# Acceder a la documentación
# Swagger UI: http://localhost:5000/swagger
# Health Check: http://localhost:5000/

# Probar la API
python src/test_api.py
```

#### Opción 2: Procesamiento Directo

```bash
# Configurar proyecto
export GOOGLE_CLOUD_PROJECT="newry-dev"

# Ejecutar procesamiento
python src/test_local.py
```

### Cloud Run

```bash
# Desplegar
gcloud run deploy compliance-newry \
  --source . \
  --set-env-vars GOOGLE_CLOUD_PROJECT=newry-dev \
  --region us-central1
```

## API REST

### Endpoints Disponibles

- **`GET /`** - Health check de la API
- **`POST /api/v1/process-emails`** - Procesar correos de compliance
- **`GET /swagger`** - Documentación Swagger/OpenAPI

### Ejemplos de Uso

#### Procesar Correos
```bash
curl -X POST http://localhost:5000/api/v1/process-emails \
  -H "Content-Type: application/json"
```

### Documentación Interactiva

Accede a la documentación completa en: http://localhost:5000/swagger

## Monitoreo

### Cloud Logging

Para ver los logs de la aplicación, usa este filtro en Google Cloud Console:

```
resource.type="global" AND logName="projects/newry-dev/logs/compliance-newry"
```

**URL directa:** https://console.cloud.google.com/logs/query?project=newry-dev&query=resource.type%3D%22global%22%20AND%20logName%3D%22projects%2Fnewry-dev%2Flogs%2Fcompliance-newry%22

### Filtros Adicionales

- **Solo ejecuciones:** `jsonPayload.event_type="execution_start" OR jsonPayload.event_type="execution_end"`
- **Solo errores:** `severity>=ERROR`
- **Correos procesados:** `jsonPayload.event_type="correo_processed"`

## Estructura del Proyecto

```
src/
├── app.py                 # API REST con Swagger
├── main.py                # Función principal
├── config.py              # Configuración con Secret Manager
├── gmail_utils.py         # Utilidades de Gmail
├── vertex_utils.py        # Integración con Vertex AI
├── bigquery_utils.py      # Operaciones BigQuery
├── postgres_utils.py      # Operaciones PostgreSQL
├── execution_control.py   # Control de ejecuciones
├── cloud_logging.py       # Sistema de logging
├── test_api.py            # Pruebas de la API
└── test_local.py          # Pruebas locales
```

## Base de Datos

### Tabla de Control: ComplianceEjecuciones

```sql
CREATE TABLE compliance_db."ComplianceEjecuciones" (
  id VARCHAR(50) PRIMARY KEY,
  FechaEjecucion TIMESTAMP NOT NULL,
  UltimaFechaCorreo TIMESTAMP,
  CorreosProcesados INTEGER NOT NULL,
  Estado VARCHAR(20) NOT NULL,
  DuracionSegundos FLOAT,
  Modo VARCHAR(20),
  FechaCreacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FechaInicioVentana TIMESTAMP,
  FechaFinVentana TIMESTAMP,
  TipoVentana VARCHAR(50) DEFAULT 'dinamica'
);
```

## Palabras Clave

El sistema filtra correos usando palabras clave específicas para compliance:

- `build issues`, `build failed`
- `stability issues`, `trending stability`
- `crash`, `crashes`, `crashlytics`
- `samsung issue report`
- `failed processing`
- `store policy`, `store guidelines`
- `developer account issues`
- `payment issues`, `billing issues`
- `performance issues`

## Modos de Ejecución

- **Primera Ejecución:** Procesa correos de las últimas 24 horas (máximo 200 correos)
- **Ventana Dinámica:** Procesa correos desde la última ejecución hasta ahora (máximo 200 correos)

## Procesamiento Paralelo

El sistema utiliza **ThreadPoolExecutor** para procesar correos en paralelo, mejorando significativamente el rendimiento:

### Configuración por Defecto:
- **5 hilos simultáneos** (configurable)
- **30 segundos timeout** por correo
- **Mejora esperada:** 80% más rápido

### Configuración:
```python
from parallel_processor import configurar_concurrencia

# Cambiar número de hilos
configurar_concurrencia(max_workers=8)

# Cambiar timeout
configurar_concurrencia(timeout=45)
```

## Rendimiento

### Comparación de Tiempos

| Configuración | Tiempo (200 correos) | Mejora |
|---------------|---------------------|---------|
| **Secuencial** | ~220 segundos | - |
| **Paralelo (3 hilos)** | ~73 segundos | 67% |
| **Paralelo (5 hilos)** | ~44 segundos | 80% |
| **Paralelo (8 hilos)** | ~28 segundos | 87% |

### Optimizaciones Implementadas

1. **ThreadPoolExecutor** - Procesamiento paralelo de correos
2. **Thread-safe operations** - Locks para operaciones de base de datos
3. **Timeout management** - Evita bloqueos indefinidos
4. **Error handling** - Manejo robusto de errores por hilo

## Troubleshooting

### Error de Cloud Logging
```bash
# Verificar credenciales
gcloud auth application-default login

# Verificar proyecto
echo $GOOGLE_CLOUD_PROJECT
```

### Error de Secret Manager
```bash
# Verificar permisos
gcloud projects get-iam-policy newry-dev
```

### Problemas de Paralelización
```python
# Reducir hilos si hay errores de API
from parallel_processor import configurar_concurrencia
configurar_concurrencia(max_workers=3)

# Aumentar timeout si hay timeouts frecuentes
configurar_concurrencia(timeout=60)
```

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request 