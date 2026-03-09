import datetime
from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import requests
import pandas as pd
import json

# URL de la API de Socrata (Datos Abiertos Colombia)
# Base de datos de origen: "Incidentes viales" (Usemos datos de Medellín, por ejemplo "yvqg-xvx2" u otra ciudad disponible). 
# Para este portafolio usaremos "yvqg-xvx2" que corresponde a Secretaria de Movilidad de Medellín - Incidentes
API_URL = "https://www.datos.gov.co/resource/yvqg-xvx2.json?$limit=1000&$order=fecha%20DESC"

default_args = {
    'owner': 'jcardonr',
    'depends_on_past': False,
    'start_date': datetime.datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def extract_data(**kwargs):
    """Extrae datos de la API pública Socrata."""
    print(f"Extrayendo datos de: {API_URL}")
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
    
    # Guardar en XCom para la siguiente tarea
    kwargs['ti'].xcom_push(key='raw_data', value=json.dumps(data))
    print(f"Número de registros obtenidos: {len(data)}")

def transform_data(**kwargs):
    """Transforma el JSON en un DataFrame de Pandas, limpia y normaliza datos."""
    ti = kwargs['ti']
    raw_data_str = ti.xcom_pull(key='raw_data', task_ids='extract_task')
    data = json.loads(raw_data_str)
    
    df = pd.DataFrame(data)
    print("Columnas originales:", df.columns)
    
    # Seleccionar y renombrar campos relevantes de la base de Medellín (Ejemplo)
    # Dependiendo de la estructura del JSON, adaptaremos las columnas a la BBDD
    column_mapping = {
        'fecha': 'fecha_accidente',
        'hora': 'hora_accidente',
        'gravedad': 'gravedad_accidente',
        'clase_incidente': 'clase_accidente',
        'direccion': 'lugar_accidente',
        'comuna': 'comuna',
        'barrio': 'barrio',
        'latitud': 'latitud',
        'longitud': 'longitud'
    }
    
    # Intersecar columnas para evitar KeyError si cambian en la API
    cols_to_keep = [c for c in column_mapping.keys() if c in df.columns]
    df = df[cols_to_keep]
    df.rename(columns=column_mapping, inplace=True)
    
    # Limpieza básica
    # Convertir a datetime y luego string para postgres
    if 'fecha_accidente' in df.columns:
        df['fecha_accidente'] = pd.to_datetime(df['fecha_accidente']).dt.date.astype(str)
    
    # Filas con lat/long inválidos ponerlas como Nulasy luego rellenar a 0 para el mapa (o descartar)
    if 'latitud' in df.columns and 'longitud' in df.columns:
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df.dropna(subset=['latitud', 'longitud'], inplace=True)

    # Convertir a dict y subir a XCom
    clean_data = df.to_dict('records')
    ti.xcom_push(key='clean_data', value=json.dumps(clean_data))
    print(f"Registros después de limpieza: {len(clean_data)}")

def load_data(**kwargs):
    """Carga los datos limpios a PostgreSQL usando ON CONFLICT para evitar exact duplicates."""
    ti = kwargs['ti']
    clean_data_str = ti.xcom_pull(key='clean_data', task_ids='transform_task')
    data = json.loads(clean_data_str)
    
    if not data:
        print("No hay datos para cargar.")
        return

    df = pd.DataFrame(data)
    
    # La conexión a BBDD que configuramos en docker compose
    # Opcional: configurar Connection Id en la UI de Airflow, usamos 'dw_postgres'
    pg_hook = PostgresHook(postgres_conn_id='dw_postgres')
    
    insert_query = """
    INSERT INTO public.accidentes_transito (
        fecha_accidente, hora_accidente, gravedad_accidente, class_accidente, 
        lugar_accidente, comuna, barrio, latitud, longitud
    ) VALUES %s
    ON CONFLICT (fecha_accidente, hora_accidente, latitud, longitud) DO NOTHING;
    """
    
    # Preparar records para execute_values
    rows = []
    for _, row in df.iterrows():
        # Usamos .get() con valores default en caso de que alguna columna falte
        rows.append((
            row.get('fecha_accidente'),
            row.get('hora_accidente'),
            row.get('gravedad_accidente', 'DESCONOCIDO'),
            row.get('clase_accidente', 'DESCONOCIDO'),
            row.get('lugar_accidente', 'DESCONOCIDO'),
            row.get('comuna', 'SIN COMUNA'),
            row.get('barrio', 'SIN BARRIO'),
            row.get('latitud'),
            row.get('longitud')
        ))
    
    from psycopg2.extras import execute_values
    
    # Execute transaction
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    try:
        # Arreglo menor en la query 'class_accidente' -> 'clase_accidente'
        insert_query = """
        INSERT INTO public.accidentes_transito (
            fecha_accidente, hora_accidente, gravedad_accidente, clase_accidente, 
            lugar_accidente, comuna, barrio, latitud, longitud
        ) VALUES %s
        ON CONFLICT (fecha_accidente, hora_accidente, latitud, longitud) DO NOTHING;
        """
        execute_values(cursor, insert_query, rows)
        conn.commit()
        print(f"Carga exitosa! Se han insertado/ignorado {len(rows)} registros.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

with DAG(
    'open_data_etl_accidentes',
    default_args=default_args,
    description='ETL pipeline para obtener accidentes de tránsito de Datos Abiertos Colombia',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['portafolio', 'datos_abiertos'],
) as dag:

    extract_task = PythonOperator(
        task_id='extract_task',
        python_callable=extract_data,
        provide_context=True,
    )

    transform_task = PythonOperator(
        task_id='transform_task',
        python_callable=transform_data,
        provide_context=True,
    )

    load_task = PythonOperator(
        task_id='load_task',
        python_callable=load_data,
        provide_context=True,
    )

    extract_task >> transform_task >> load_task
