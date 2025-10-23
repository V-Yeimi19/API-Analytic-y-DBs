import os
import boto3
import pandas as pd
from sqlalchemy import create_engine
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import logging
from datetime import datetime

# ==== LOGGING ====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ==== ENV ====
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DATABASE")

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE")

AWS_REGION = os.getenv("AWS_DEFAULT_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
AWS_SESSION_TOKEN= os.getenv("AWS_SESSION_TOKEN")
LOCAL_DATA_DIR = os.getenv("LOCAL_DATA_DIR", "/data/output")

# ==== AWS CLIENTS ====
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=AWS_SESSION_TOKEN
)

glue = boto3.client(
    "glue",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=AWS_SESSION_TOKEN
)

# ==== FUNCIONES ====

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def upload_to_s3(local_path, s3_path):
    try:
        s3.upload_file(local_path, S3_BUCKET, s3_path)
        logging.info(f"✅ Subido a S3: s3://{S3_BUCKET}/{s3_path}")
    except Exception as e:
        logging.error(f"❌ Error subiendo {local_path} a S3: {e}")

def create_glue_database():
    """Crea la base de datos en AWS Glue si no existe"""
    database_name = "primac_analytics_db"
    try:
        glue.get_database(Name=database_name)
        logging.info(f"✅ Database '{database_name}' ya existe en Glue")
    except glue.exceptions.EntityNotFoundException:
        glue.create_database(
            DatabaseInput={
                'Name': database_name,
                'Description': 'Database para análisis de datos Primac desde S3'
            }
        )
        logging.info(f"✅ Database '{database_name}' creada en Glue")
    except Exception as e:
        logging.error(f"❌ Error creando database en Glue: {e}")

def create_glue_table(database_name, table_name, s3_location, columns):
    """Crea o actualiza una tabla en el catálogo de AWS Glue"""
    try:
        # Construir definición de columnas
        storage_descriptor = {
            'Columns': columns,
            'Location': f"s3://{S3_BUCKET}/{s3_location}",
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
                'Parameters': {
                    'field.delim': ',',
                    'skip.header.line.count': '1'
                }
            }
        }

        # Intentar actualizar la tabla si existe
        try:
            glue.update_table(
                DatabaseName=database_name,
                TableInput={
                    'Name': table_name,
                    'StorageDescriptor': storage_descriptor,
                    'TableType': 'EXTERNAL_TABLE'
                }
            )
            logging.info(f"✅ Tabla '{table_name}' actualizada en Glue")
        except glue.exceptions.EntityNotFoundException:
            # Si no existe, crear nueva tabla
            glue.create_table(
                DatabaseName=database_name,
                TableInput={
                    'Name': table_name,
                    'StorageDescriptor': storage_descriptor,
                    'TableType': 'EXTERNAL_TABLE'
                }
            )
            logging.info(f"✅ Tabla '{table_name}' creada en Glue")
    except Exception as e:
        logging.error(f"❌ Error creando tabla {table_name} en Glue: {e}")

def infer_glue_columns(df, table_name):
    """Infiere el esquema de columnas para Glue desde un DataFrame"""
    type_mapping = {
        'int64': 'bigint',
        'int32': 'int',
        'float64': 'double',
        'float32': 'float',
        'bool': 'boolean',
        'object': 'string',
        'datetime64[ns]': 'timestamp'
    }

    columns = []
    for col in df.columns:
        dtype_str = str(df[col].dtype)
        glue_type = type_mapping.get(dtype_str, 'string')
        columns.append({
            'Name': col.lower().replace(' ', '_'),
            'Type': glue_type
        })

    return columns

def export_mysql():
    try:
        database_name = "primac_analytics_db"
        engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
        tables = pd.read_sql("SHOW TABLES;", engine)
        for t in tables.iloc[:, 0]:
            df = pd.read_sql(f"SELECT * FROM {t};", engine)
            local_dir = os.path.join(LOCAL_DATA_DIR, "mysql", t)
            ensure_dir(local_dir)
            local_file = os.path.join(local_dir, f"{t}.csv")
            df.to_csv(local_file, index=False)
            s3_path = f"mysql/{t}/{t}.csv"
            upload_to_s3(local_file, s3_path)

            # Crear tabla en Glue Catalog
            columns = infer_glue_columns(df, t)
            table_name = f"mysql_{t}"
            create_glue_table(database_name, table_name, f"mysql/{t}/", columns)

        logging.info("✅ Exportación MySQL completada.")
    except Exception as e:
        logging.error(f"❌ Error en export_mysql: {e}")

def export_postgres():
    try:
        database_name = "primac_analytics_db"
        engine = create_engine(f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
        query_tables = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public';
        """
        tables = pd.read_sql(query_tables, engine)
        for t in tables["table_name"]:
            df = pd.read_sql(f"SELECT * FROM {t};", engine)
            local_dir = os.path.join(LOCAL_DATA_DIR, "postgres", t)
            ensure_dir(local_dir)
            local_file = os.path.join(local_dir, f"{t}.csv")
            df.to_csv(local_file, index=False)
            s3_path = f"postgres/{t}/{t}.csv"
            upload_to_s3(local_file, s3_path)

            # Crear tabla en Glue Catalog
            columns = infer_glue_columns(df, t)
            table_name = f"postgresql_{t}"
            create_glue_table(database_name, table_name, f"postgres/{t}/", columns)

        logging.info("✅ Exportación PostgreSQL completada.")
    except Exception as e:
        logging.error(f"❌ Error en export_postgres: {e}")

def export_cassandra():
    try:
        database_name = "primac_analytics_db"
        cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
        session = cluster.connect(CASSANDRA_KEYSPACE)
        tables_query = f"SELECT table_name FROM system_schema.tables WHERE keyspace_name = '{CASSANDRA_KEYSPACE}';"
        rows = session.execute(tables_query)
        for row in rows:
            t = row.table_name
            df = pd.DataFrame(list(session.execute(f"SELECT * FROM {t};")))
            if df.empty:
                continue
            local_dir = os.path.join(LOCAL_DATA_DIR, "cassandra", t)
            ensure_dir(local_dir)
            local_file = os.path.join(local_dir, f"{t}.csv")
            df.to_csv(local_file, index=False)
            s3_path = f"cassandra/{t}/{t}.csv"
            upload_to_s3(local_file, s3_path)

            # Crear tabla en Glue Catalog
            columns = infer_glue_columns(df, t)
            table_name = f"cassandra_{t}"
            create_glue_table(database_name, table_name, f"cassandra/{t}/", columns)

        logging.info("✅ Exportación Cassandra completada.")
    except Exception as e:
        logging.error(f"❌ Error en export_cassandra: {e}")

def main():
    start_time = datetime.now()
    logging.info("🚀 Iniciando proceso de ingesta...")

    # Crear base de datos en AWS Glue
    logging.info("📊 Creando catálogo en AWS Glue...")
    create_glue_database()

    # Ejecutar exportaciones
    export_mysql()
    export_postgres()
    export_cassandra()

    elapsed = (datetime.now() - start_time).total_seconds()
    logging.info(f"🎯 Ingesta completada en {elapsed:.2f} segundos")
    logging.info("📊 Catálogo de datos disponible en AWS Glue: primac_analytics_db")

if __name__ == "__main__":
    main()

