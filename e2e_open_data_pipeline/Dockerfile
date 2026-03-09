FROM apache/airflow:2.8.1

# Cambiar a usuario root para instalar dependencias de sistema operativo si fuera necesario
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         build-essential \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Volver al usuario airflow
USER airflow

# Instalar los requerimientos de Python para Airflow
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt
