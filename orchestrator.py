#!/usr/bin/env python3
"""
Orquestador Principal - Proyecto Primac S3 Analytics
====================================================

Gestiona todas las bases de datos del proyecto:
- MySQL (BD_Users_Primac) 
- PostgreSQL (proyecto_postgresql)
- Cassandra (Primac-Claims-Payments-DB)

Uso: python orchestrator.py [comando]
"""

import subprocess
import sys
import time
import os
from typing import Optional

# Configuración
COMPOSE_FILE = "docker-compose.yml"
PROJECT_NAME = "primac-s3-analytics"

# Colores para output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def colored_print(message: str, color: str = Colors.ENDC) -> None:
    """Imprime mensajes con color"""
    print(f"{color}{message}{Colors.ENDC}")

def run_command(cmd: str, detach: bool = False, show_output: bool = True) -> int:
    """Ejecuta un comando y devuelve el código de salida"""
    if show_output:
        colored_print(f"👉 {cmd}", Colors.BLUE)
    
    try:
        if detach:
            process = subprocess.Popen(cmd, shell=True)
            return process.returncode
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode
    except KeyboardInterrupt:
        colored_print("\n❌ Operación cancelada por el usuario", Colors.RED)
        sys.exit(1)
    except Exception as e:
        colored_print(f"❌ Error ejecutando comando: {e}", Colors.RED)
        return 1

def wait_for_service(service_name: str, check_cmd: str, max_attempts: int = 30, interval: int = 5) -> bool:
    """Espera hasta que un servicio esté disponible"""
    colored_print(f"⏳ Esperando a {service_name}...", Colors.YELLOW)
    
    for attempt in range(max_attempts):
        try:
            result = subprocess.run(
                check_cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                colored_print(f"✅ {service_name} está listo", Colors.GREEN)
                return True
        except Exception:
            pass
        
        if attempt < max_attempts - 1:
            colored_print(f"Esperando {service_name}... intento {attempt + 1}/{max_attempts}", Colors.YELLOW)
            time.sleep(interval)
    
    colored_print(f"❌ {service_name} no está disponible después de {max_attempts * interval} segundos", Colors.RED)
    return False

def wait_for_mysql() -> bool:
    """Espera hasta que MySQL esté listo"""
    return wait_for_service(
        "MySQL",
        "docker exec primac_mysql_db mysqladmin ping -u admin -padmin --silent"
    )

def wait_for_postgresql() -> bool:
    """Espera hasta que PostgreSQL esté listo"""
    return wait_for_service(
        "PostgreSQL", 
        "docker exec primac_postgresql_db pg_isready -U postgres"
    )

def wait_for_cassandra() -> bool:
    """Espera hasta que Cassandra esté healthy"""
    return wait_for_service(
        "Cassandra",
        "docker inspect --format='{{.State.Health.Status}}' primac_cassandra_db | grep healthy"
    )

def check_docker() -> bool:
    """Verifica que Docker esté disponible"""
    try:
        result = subprocess.run("docker --version", shell=True, capture_output=True)
        if result.returncode != 0:
            colored_print("❌ Docker no está disponible", Colors.RED)
            return False
        return True
    except Exception:
        colored_print("❌ Docker no está instalado o no está disponible", Colors.RED)
        return False

def check_compose_file() -> bool:
    """Verifica que el archivo docker-compose.yml existe"""
    if not os.path.exists(COMPOSE_FILE):
        colored_print(f"❌ No se encontró {COMPOSE_FILE}", Colors.RED)
        return False
    return True

def show_status() -> None:
    """Muestra el estado de todos los servicios"""
    colored_print("\n📊 Estado de los servicios:", Colors.HEADER)
    
    services = [
        ("primac_mysql_db", "MySQL"),
        ("primac_postgresql_db", "PostgreSQL"), 
        ("primac_cassandra_db", "Cassandra"),
        ("primac_data_science_api", "Data Science API")
    ]
    
    for container_name, service_name in services:
        try:
            result = subprocess.run(
                f"docker inspect --format='{{{{.State.Status}}}}' {container_name}",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                status = result.stdout.strip()
                if status == "running":
                    colored_print(f"✅ {service_name}: {status}", Colors.GREEN)
                else:
                    colored_print(f"⚠️  {service_name}: {status}", Colors.YELLOW)
            else:
                colored_print(f"❌ {service_name}: no encontrado", Colors.RED)
        except Exception:
            colored_print(f"❌ {service_name}: error al verificar", Colors.RED)

def start_all_databases() -> None:
    """Inicia todas las bases de datos con configuración completa"""
    colored_print("🚀 Iniciando todas las bases de datos...", Colors.HEADER)
    
    # Levantar bases de datos
    if run_command(f"docker compose -f {COMPOSE_FILE} up -d mysql-db postgresql-db cassandra-db") != 0:
        colored_print("❌ Error iniciando las bases de datos", Colors.RED)
        sys.exit(1)
    
    # Esperar que todas estén listas
    success = True
    success &= wait_for_mysql()
    success &= wait_for_postgresql() 
    success &= wait_for_cassandra()
    
    if not success:
        colored_print("❌ No todas las bases de datos están disponibles", Colors.RED)
        sys.exit(1)
    
    # Ejecutar setup de Cassandra si existe
    colored_print("⚙️ Configurando Cassandra schema...", Colors.YELLOW)
    run_command(f"docker compose -f {COMPOSE_FILE} up cassandra-setup")
    
    colored_print("✅ Todas las bases de datos están listas y configuradas", Colors.GREEN)

def start_individual_service(service: str) -> None:
    """Inicia un servicio individual"""
    service_map = {
        "mysql": "mysql-db",
        "postgresql": "postgresql-db", 
        "cassandra": "cassandra-db",
        "api": "data-science-api"
    }
    
    if service not in service_map:
        colored_print(f"❌ Servicio '{service}' no reconocido", Colors.RED)
        return
    
    docker_service = service_map[service]
    colored_print(f"🚀 Iniciando {service}...", Colors.HEADER)
    
    if run_command(f"docker compose -f {COMPOSE_FILE} up -d {docker_service}") != 0:
        colored_print(f"❌ Error iniciando {service}", Colors.RED)
        return
    
    # Esperar que esté listo
    if service == "mysql" and not wait_for_mysql():
        return
    elif service == "postgresql" and not wait_for_postgresql():
        return
    elif service == "cassandra" and not wait_for_cassandra():
        return
    
    colored_print(f"✅ {service} iniciado correctamente", Colors.GREEN)

def stop_all() -> None:
    """Detiene todos los servicios"""
    colored_print("🛑 Deteniendo todos los servicios...", Colors.YELLOW)
    run_command(f"docker compose -f {COMPOSE_FILE} down")
    colored_print("✅ Servicios detenidos", Colors.GREEN)

def cleanup() -> None:
    """Limpia contenedores, volúmenes y redes"""
    colored_print("🧹 Limpiando contenedores, volúmenes y redes...", Colors.YELLOW)
    run_command(f"docker compose -f {COMPOSE_FILE} down -v --remove-orphans")
    colored_print("✅ Limpieza completada", Colors.GREEN)

def show_logs(service: Optional[str] = None) -> None:
    """Muestra logs de los servicios"""
    if service:
        colored_print(f"📋 Mostrando logs de {service}:", Colors.HEADER)
        run_command(f"docker compose -f {COMPOSE_FILE} logs -f {service}")
    else:
        colored_print("📋 Mostrando logs de todos los servicios:", Colors.HEADER)
        run_command(f"docker compose -f {COMPOSE_FILE} logs -f")

def show_help() -> None:
    """Muestra la ayuda del programa"""
    help_text = f"""
{Colors.HEADER}{Colors.BOLD}Orquestador Principal - Proyecto Primac S3 Analytics{Colors.ENDC}

{Colors.BLUE}COMANDOS PRINCIPALES:{Colors.ENDC}
  {Colors.GREEN}all{Colors.ENDC}                 - Inicia todas las bases de datos + configuración
  {Colors.GREEN}mysql{Colors.ENDC}               - Solo MySQL  
  {Colors.GREEN}postgresql{Colors.ENDC}          - Solo PostgreSQL
  {Colors.GREEN}cassandra{Colors.ENDC}           - Solo Cassandra
  {Colors.GREEN}api{Colors.ENDC}                 - Solo Data Science API

{Colors.BLUE}COMANDOS DE GESTIÓN:{Colors.ENDC}
  {Colors.GREEN}status{Colors.ENDC}              - Muestra el estado de todos los servicios
  {Colors.GREEN}stop{Colors.ENDC}                - Detiene todos los servicios
  {Colors.GREEN}cleanup{Colors.ENDC}             - Limpia contenedores, volúmenes y redes
  {Colors.GREEN}logs [servicio]{Colors.ENDC}     - Muestra logs (todos o de un servicio específico)
  {Colors.GREEN}help{Colors.ENDC}                - Muestra esta ayuda

{Colors.BLUE}EJEMPLOS:{Colors.ENDC}
  python orchestrator.py all           # Inicia todo el stack
  python orchestrator.py mysql         # Solo MySQL
  python orchestrator.py status        # Ver estado
  python orchestrator.py logs mysql-db # Logs de MySQL
  python orchestrator.py cleanup       # Limpiar todo

{Colors.YELLOW}SERVICIOS DISPONIBLES:{Colors.ENDC}
  • MySQL (puerto 3307)
  • PostgreSQL (puerto 5432) 
  • Cassandra (puerto 9042)
  • Data Science API (puerto 8000)
  • Adminer (puerto 8081)
  • pgAdmin (puerto 8082)
"""
    print(help_text)

def main():
    """Función principal"""
    # Verificaciones iniciales
    if not check_docker():
        sys.exit(1)
    
    if not check_compose_file():
        sys.exit(1)
    
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # Procesar comandos
    if command == "all":
        start_all_databases()
        
    elif command in ["mysql", "postgresql", "cassandra", "api"]:
        start_individual_service(command)
        
    elif command == "status":
        show_status()
        
    elif command == "stop":
        stop_all()
        
    elif command == "cleanup":
        cleanup()
        
    elif command == "logs":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        show_logs(service)
        
    elif command in ["help", "--help", "-h"]:
        show_help()
        
    else:
        colored_print(f"❌ Comando '{command}' no reconocido", Colors.RED)
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        colored_print("\n👋 ¡Hasta luego!", Colors.YELLOW)
        sys.exit(0)
    except Exception as e:
        colored_print(f"❌ Error inesperado: {e}", Colors.RED)
        sys.exit(1)