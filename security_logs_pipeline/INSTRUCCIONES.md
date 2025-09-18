# 🛡️ Instrucciones de Instalación y Uso - Pipeline de Seguridad

## Prerrequisitos

1. **Docker Desktop** instalado y corriendo
2. **16GB RAM** mínimo recomendado (el stack ELK consume recursos)
3. **Git** para clonar el repositorio
4. **Puertos disponibles**: 5601, 9200, 9092, 8080, 8081, 8082, 443

## 🔧 Configuración Inicial

### 1. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
copy .env.example .env

# Editar .env con tus configuraciones
notepad .env
```

**Configuraciones importantes:**
- **Slack Webhook**: Para alertas en tiempo real
- **Email SMTP**: Para notificaciones críticas
- **PagerDuty**: Para alertas de alta severidad (opcional)

### 2. Iniciar el Pipeline

```bash
# Construir y levantar todos los servicios
docker-compose up -d

# Verificar que todos los servicios estén corriendo
docker-compose ps
```

**⏳ Tiempo de inicio**: 5-10 minutos (Elasticsearch tarda en inicializar)

### 3. Verificar Servicios

```bash
# Ver logs de inicialización
docker-compose logs -f elasticsearch
docker-compose logs -f kibana
docker-compose logs -f logstash
```

## 🌐 Acceso a Interfaces

Una vez que todos los servicios estén corriendo:

| Servicio | URL | Credenciales | Propósito |
|----------|-----|--------------|-----------|
| **Kibana** | http://localhost:5601 | elastic / password | Dashboards y búsquedas |
| **Wazuh Dashboard** | https://localhost:443 | admin / admin | SIEM completo |
| **Elasticsearch** | http://localhost:9200 | elastic / password | API de datos |
| **Kafka UI** | http://localhost:8080 | - | Monitoreo streaming |
| **Airflow** | http://localhost:8081 | admin / admin | Orquestación |
| **Storm UI** | http://localhost:8082 | - | Procesamiento tiempo real |

## 🚀 Uso del Pipeline

### 1. Activar Pipeline en Airflow

1. Ve a http://localhost:8081
2. Inicia sesión con admin/admin
3. Activa el DAG `security_logs_pipeline`
4. El pipeline comenzará a procesar logs automáticamente

### 2. Generar Logs de Prueba

El sistema incluye un generador de logs sintéticos que simula:
- **Logs web** (Apache/Nginx)
- **Logs de firewall** (iptables)
- **Logs de autenticación** (SSH/RDP)
- **Logs de sistema** (Windows Events)
- **Logs DNS** (BIND)

```bash
# Ver logs generados
docker-compose logs -f log-generator

# Verificar archivos de logs
docker-compose exec log-generator ls -la /app/logs/
```

### 3. Monitorear en Kibana

1. Ve a http://localhost:5601
2. Inicia sesión con elastic/password
3. Ve a **Discover** para explorar logs
4. Ve a **Dashboard** para métricas visuales

#### Índices principales:
- `security-logs-*`: Logs procesados
- `security-alerts-*`: Alertas generadas

### 4. Configurar Dashboards

```bash
# Importar dashboards predefinidos
curl -X POST "localhost:5601/api/saved_objects/_import" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  --form file=@dashboards/kibana/security-dashboard.ndjson
```

## 🤖 Machine Learning y Detección

### Modelos Incluidos

1. **Isolation Forest**: Detección de anomalías generales
2. **Clustering**: Agrupación de patrones de ataque
3. **Time Series**: Análisis de tendencias temporales

### Entrenar Modelos

```bash
# Entrenar con datos históricos
docker-compose exec ml-processor python ml_models/model_trainer.py

# Ver métricas de entrenamiento
docker-compose logs ml-processor
```

### Ajustar Umbrales

Edita `.env`:
```
ANOMALY_THRESHOLD=0.8          # Umbral de anomalía (0-1)
BRUTE_FORCE_THRESHOLD=10       # Intentos fallidos para brute force
SUSPICIOUS_IP_THRESHOLD=50     # Requests por minuto sospechosos
```

## 🚨 Sistema de Alertas

### Tipos de Alertas

#### Críticas (Respuesta Inmediata)
- Intrusión confirmada
- Malware detectado
- Exfiltración de datos

#### Altas (< 1 hora)
- Ataques de fuerza bruta
- Escaneo de puertos masivo
- Inyección SQL detectada

#### Medias (< 4 horas)
- Comportamiento anómalo de usuario
- Acceso fuera de horario
- Múltiples errores 4xx/5xx

### Configurar Notificaciones

#### Slack
```bash
# En .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#security-alerts
```

#### Email
```bash
# En .env
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_RECIPIENTS=security-team@company.com,soc@company.com
```

## 🔍 Análisis y Investigación

### Búsquedas Comunes en Kibana

```json
// Ataques web en las últimas 24h
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-24h"}}},
        {"terms": {"tags": ["web_attack", "sql_injection_attempt"]}}
      ]
    }
  }
}

// IPs con más intentos fallidos
{
  "aggs": {
    "failed_attempts": {
      "terms": {
        "field": "source_ip",
        "size": 10
      },
      "aggs": {
        "failures": {
          "filter": {"term": {"result": "FAILED"}}
        }
      }
    }
  }
}

// Anomalías detectadas por ML
{
  "query": {
    "bool": {
      "must": [
        {"term": {"alert_type": "anomaly_detected"}},
        {"range": {"anomaly_score": {"gte": 0.8}}}
      ]
    }
  }
}
```

### Investigar Incidentes

1. **Identificar la alerta** en Kibana o Wazuh
2. **Buscar eventos relacionados** por IP/usuario/tiempo
3. **Analizar patrones** usando visualizaciones
4. **Correlacionar** con otras fuentes de datos
5. **Documentar** hallazgos y acciones tomadas

## 📊 Reportes y Métricas

### Generar Reportes Automáticos

```bash
# Reporte diario de seguridad
docker-compose exec airflow-webserver python /opt/airflow/src/utils/security_reporter.py

# Métricas de rendimiento
curl -X GET "localhost:9200/security-logs-*/_stats"
```

### KPIs Principales

- **Volumen de logs**: Logs procesados por minuto
- **Tasa de alertas**: Alertas por hora/día
- **Tiempo de respuesta**: Latencia de procesamiento
- **Precisión ML**: Tasa de falsos positivos/negativos
- **Cobertura**: Tipos de amenazas detectadas

## 🛠️ Troubleshooting

### Problemas Comunes

#### Elasticsearch no inicia
```bash
# Verificar memoria disponible
docker stats

# Aumentar memoria virtual
sudo sysctl -w vm.max_map_count=262144

# Reiniciar servicio
docker-compose restart elasticsearch
```

#### Logstash no procesa logs
```bash
# Verificar configuración
docker-compose exec logstash logstash --config.test_and_exit

# Ver logs de error
docker-compose logs logstash
```

#### Kafka no recibe mensajes
```bash
# Verificar topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Ver mensajes en topic
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic raw-security-logs \
  --from-beginning
```

### Comandos Útiles

```bash
# Ver estado de todos los servicios
docker-compose ps

# Reiniciar servicio específico
docker-compose restart <servicio>

# Ver logs en tiempo real
docker-compose logs -f <servicio>

# Limpiar y reiniciar todo
docker-compose down -v
docker-compose up -d
```

## 🔒 Seguridad del Pipeline

### Mejores Prácticas

1. **Cambiar contraseñas por defecto**
2. **Configurar HTTPS** para interfaces web
3. **Implementar autenticación** robusta
4. **Segregar redes** de producción
5. **Cifrar datos sensibles** en tránsito y reposo
6. **Auditar accesos** regularmente

### Hardening

```bash
# Cambiar contraseñas de Elasticsearch
curl -X POST "localhost:9200/_security/user/elastic/_password" \
  -H "Content-Type: application/json" \
  -d '{"password": "new-strong-password"}'

# Configurar SSL/TLS
# Editar docker-compose.yml para habilitar SSL
```

## 📈 Escalabilidad

### Para Entornos de Producción

1. **Cluster Elasticsearch**: Múltiples nodos
2. **Kafka Cluster**: Alta disponibilidad
3. **Load Balancers**: Distribución de carga
4. **Monitoring**: Prometheus + Grafana
5. **Backup**: Snapshots automáticos

### Optimización de Rendimiento

```bash
# Ajustar configuración de Elasticsearch
# En docker-compose.yml:
ES_JAVA_OPTS: "-Xms4g -Xmx4g"

# Optimizar índices
curl -X POST "localhost:9200/security-logs-*/_forcemerge?max_num_segments=1"
```

## 🎯 Casos de Uso Empresariales

### Compliance y Auditoría
- **PCI-DSS**: Monitoreo de transacciones
- **HIPAA**: Protección de datos médicos
- **SOX**: Auditoría de accesos financieros
- **GDPR**: Detección de brechas de datos

### Detección de Amenazas
- **APTs**: Ataques persistentes avanzados
- **Insider Threats**: Amenazas internas
- **Malware**: Detección de código malicioso
- **Data Exfiltration**: Fuga de información

## 🆘 Soporte

Si encuentras problemas:

1. **Verifica logs** de servicios específicos
2. **Consulta documentación** de cada componente
3. **Revisa configuración** de red y puertos
4. **Valida recursos** de sistema (RAM, CPU, disco)

## 🎉 ¡Pipeline Listo!

Tu pipeline de análisis de logs de seguridad está funcionando. Ahora puedes:

- ✅ **Procesar logs** en tiempo real
- ✅ **Detectar amenazas** con ML
- ✅ **Generar alertas** automáticas
- ✅ **Investigar incidentes** eficientemente
- ✅ **Cumplir normativas** de seguridad

¡Perfecto para roles en ciberseguridad y SOC!