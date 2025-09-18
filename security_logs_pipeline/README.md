# Pipeline de Análisis de Logs y Seguridad en Tiempo Real

## 🛡️ Objetivo

Construir un sistema completo de Security Information and Event Management (SIEM) que procese logs de seguridad en tiempo real, detecte amenazas usando Machine Learning, y genere alertas automáticas para respuesta rápida a incidentes de seguridad.

## 🏗️ Arquitectura

```
Logs Sources → Filebeat → Logstash → Kafka → Storm → ML Models → Elasticsearch → Kibana/Wazuh
     ↓            ↓         ↓         ↓       ↓         ↓            ↓           ↓
  Servidores   Colección  Parsing  Buffer  Análisis  Detección   Indexado   Visualización
   Firewall    Normaliz.  Enrich.  Stream  Tiempo    Anomalías   Búsqueda    Alertas
   Apps Web                        Real    Real      ML Models   Histórico   Dashboards
```

## 🛠️ Stack Tecnológico

- **Colección**: Filebeat + Logstash (ELK Stack)
- **Streaming**: Apache Kafka + Apache Storm
- **Machine Learning**: Scikit-learn + Isolation Forest + LSTM
- **SIEM**: Elasticsearch + Kibana + Wazuh
- **Alertas**: ElastAlert + Slack/Email notifications
- **Orquestación**: Apache Airflow
- **Infraestructura**: Docker Compose + Kubernetes ready

## 🎯 Casos de Uso

### 1. **Detección de Intrusiones**
- Análisis de logs de firewall y IDS/IPS
- Detección de patrones de ataque (brute force, port scanning)
- Identificación de IPs maliciosas y comportamientos anómalos

### 2. **Análisis de Logs Web**
- Detección de ataques web (SQL injection, XSS, CSRF)
- Análisis de tráfico sospechoso y bots maliciosos
- Monitoreo de códigos de error y patrones de acceso

### 3. **Monitoreo de Autenticación**
- Detección de intentos de login fallidos masivos
- Análisis de patrones de acceso inusuales
- Alertas por escalación de privilegios

### 4. **Análisis de Comportamiento**
- Detección de anomalías en patrones de usuario
- Identificación de actividad fuera de horario
- Análisis de transferencia de datos inusual

## 📊 Métricas y KPIs de Seguridad

- **Volumen**: Logs procesados por segundo/minuto
- **Latencia**: Tiempo desde log hasta alerta (< 30 segundos)
- **Precisión**: Tasa de falsos positivos/negativos
- **Cobertura**: Tipos de amenazas detectadas
- **MTTR**: Tiempo medio de respuesta a incidentes
- **Compliance**: Cumplimiento de normativas (SOX, GDPR, PCI-DSS)

## 🚨 Tipos de Alertas

### Críticas (Respuesta Inmediata)
- Intrusión confirmada
- Malware detectado
- Exfiltración de datos
- Escalación de privilegios no autorizada

### Altas (Respuesta < 1 hora)
- Múltiples intentos de login fallidos
- Acceso desde ubicaciones inusuales
- Patrones de tráfico anómalos
- Vulnerabilidades críticas explotadas

### Medias (Respuesta < 4 horas)
- Comportamiento de usuario anómalo
- Configuraciones de seguridad cambiadas
- Acceso a recursos sensibles fuera de horario

### Informativas (Revisión diaria)
- Resumen de actividad de seguridad
- Tendencias de amenazas
- Reportes de compliance

## 📁 Estructura del Proyecto

```
security_logs_pipeline/
├── docker-compose.yml              # Orquestación de servicios
├── requirements.txt                # Dependencias Python
├── .env.example                   # Variables de entorno
├── data/
│   ├── sample_logs/               # Logs de ejemplo para testing
│   └── ml_models/                 # Modelos ML entrenados
├── config/
│   ├── filebeat/                  # Configuración Filebeat
│   ├── logstash/                  # Pipelines Logstash
│   ├── elasticsearch/             # Configuración ES
│   ├── kibana/                    # Dashboards Kibana
│   └── wazuh/                     # Reglas Wazuh
├── src/
│   ├── collectors/                # Colectores de logs
│   ├── processors/                # Procesadores Storm
│   ├── ml_models/                 # Modelos de detección
│   ├── alerting/                  # Sistema de alertas
│   └── utils/                     # Utilidades comunes
├── airflow/
│   └── dags/                      # DAGs de Airflow
├── notebooks/                     # Análisis y entrenamiento ML
├── dashboards/                    # Dashboards Kibana/Grafana
├── rules/                         # Reglas de detección
└── scripts/                       # Scripts de automatización
```

## 🔧 Instalación Rápida

```bash
# Clonar y configurar
git clone <repo>
cd security_logs_pipeline
cp .env.example .env

# Configurar variables de entorno
# Editar .env con tus configuraciones

# Levantar servicios
docker-compose up -d

# Verificar servicios
docker-compose ps
```

## 🌐 Interfaces de Usuario

| Servicio | URL | Credenciales | Propósito |
|----------|-----|--------------|-----------|
| **Kibana** | http://localhost:5601 | elastic/password | Dashboards y búsquedas |
| **Wazuh** | http://localhost:443 | admin/admin | SIEM y alertas |
| **Kafka UI** | http://localhost:8080 | - | Monitoreo streaming |
| **Airflow** | http://localhost:8081 | admin/admin | Orquestación |
| **Storm UI** | http://localhost:8082 | - | Monitoreo procesamiento |

## 🎯 Características Principales

### **Detección en Tiempo Real**
- Procesamiento de logs con latencia < 30 segundos
- Análisis de patrones en ventanas deslizantes
- Correlación de eventos multi-fuente

### **Machine Learning Avanzado**
- Isolation Forest para detección de anomalías
- LSTM para análisis de secuencias temporales
- Clustering para identificación de patrones

### **Alertas Inteligentes**
- Reducción de falsos positivos con ML
- Priorización automática de alertas
- Integración con sistemas de ticketing

### **Compliance y Auditoría**
- Retención de logs según normativas
- Reportes automáticos de compliance
- Trazabilidad completa de eventos

## 📈 Valor de Negocio

Este pipeline demuestra competencias críticas en:

- **Ciberseguridad**: Detección proactiva de amenazas
- **Ingeniería de Datos**: Procesamiento de alto volumen en tiempo real
- **Machine Learning**: Aplicación de ML a problemas de seguridad
- **Compliance**: Cumplimiento de normativas de seguridad
- **DevSecOps**: Integración de seguridad en pipelines de datos

Ideal para roles en:
- **Security Engineer** / **SIEM Analyst**
- **Data Engineer** en equipos de seguridad
- **DevSecOps Engineer**
- **Cybersecurity Data Scientist**
- **SOC (Security Operations Center) roles**

## 🚀 Casos de Uso Empresariales

- **Bancos**: Detección de fraude y compliance PCI-DSS
- **E-commerce**: Protección contra ataques web y bots
- **Healthcare**: Compliance HIPAA y protección de datos sensibles
- **Gobierno**: Detección de APTs y ciberataques estatales
- **Startups**: SIEM económico y escalable

## 🔒 Seguridad del Pipeline

- Cifrado end-to-end de logs sensibles
- Autenticación y autorización granular
- Segregación de redes y accesos
- Auditoría de acceso a datos de seguridad
- Backup y recuperación de datos críticos