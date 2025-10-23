#!/usr/bin/env python3
import subprocess
import time
import os
import sys
import socket

def check_connection(host, port, timeout=5):
    """Verifica conectividad TCP con el host/puerto dado."""
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False

def wait_for_db(host, port, name):
    print(f"⏳ Esperando a que {name} ({host}:{port}) esté disponible...")
    for _ in range(60):
        if check_connection(host, port):
            print(f"✅ {name} está listo.")
            return True
        time.sleep(5)
    print(f"❌ Timeout esperando {name}.")
    return False

def run(cmd):
    print(f"👉 {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    env = os.getenv("ENVIRONMENT", "local")
    print(f"🚀 Iniciando orquestador Primac en entorno: {env.upper()}\n")

    # Cargar variables de entorno
    from dotenv import load_dotenv
    load_dotenv()

    mysql_ok = wait_for_db(os.getenv("MYSQL_HOST"), os.getenv("MYSQL_PORT"), "MySQL")
    postgres_ok = wait_for_db(os.getenv("POSTGRES_HOST"), os.getenv("POSTGRES_PORT"), "PostgreSQL")
    cassandra_ok = wait_for_db(os.getenv("CASSANDRA_HOST"), os.getenv("CASSANDRA_PORT"), "Cassandra")

    if not (mysql_ok and postgres_ok and cassandra_ok):
        print("❌ No se pudo conectar a todas las bases. Abortando.")
        sys.exit(1)

    print("\n📥 Ejecutando ingesta de datos hacia S3...")
    run("docker compose up --build ingesta")

    print("\n📊 Iniciando API analítica...")
    run("docker compose up --build -d analytics_api")

    print("\n✅ API disponible en http://localhost:8000")

if __name__ == "__main__":
    main()
