# API Analítica Primac - Microservicio de Data Science

API de análisis de datos para el sistema de seguros Primac que integra información de 3 microservicios mediante ingesta de datos a S3 y consultas con AWS Athena.

## 📋 Tabla de Contenidos

- [Descripción del Proyecto](#-descripción-del-proyecto)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Modo Desarrollo Local](#-modo-desarrollo-local)
- [Modo Producción](#-modo-producción)
- [Endpoints de la API](#-endpoints-de-la-api)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Descripción del Proyecto

Este microservicio es parte de un sistema distribuido de seguros donde cada miembro del equipo gestiona un microservicio con su propia base de datos. El microservicio analítico:

1. **Ingesta datos** del 100% de registros de 3 bases de datos (estrategia pull)
2. **Almacena** los datos en formato CSV en Amazon S3
3. **Cataloga** automáticamente los datos en AWS Glue
4. **Ejecuta queries analíticas** mediante AWS Athena
5. **Expone** resultados a través de una API REST documentada con Swagger

### Bases de Datos Integradas:

- **MySQL**: Gestión de usuarios, clientes, agentes y beneficiarios
- **PostgreSQL**: Gestión de productos, pólizas y coberturas
- **Cassandra**: Registro de reclamos, pagos y auditoría de transacciones

---

## 🏗️ Arquitectura del Sistema

### Arquitectura Completa del Equipo

```
┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│  Microservicio 1     │   │  Microservicio 2     │   │  Microservicio 3     │
│  (MySQL)             │   │  (PostgreSQL)        │   │  (Cassandra)         │
│                      │   │                      │   │                      │
│  • API REST          │   │  • API REST          │   │  • API REST          │
│  • BD MySQL          │   │  • BD PostgreSQL     │   │  • BD Cassandra      │
│  • Compañero A       │   │  • Compañero B       │   │  • Compañero C       │
└──────────┬───────────┘   └──────────┬───────────┘   └──────────┬───────────┘
           │                          │                          │
           │                          │                          │
           └──────────────────────────┴──────────────────────────┘
                                      │
                         Conexión a bases de datos remotas
                                      │
                         ┌────────────▼────────────┐
                         │                         │
                         │  TU MICROSERVICIO       │
                         │  ANALÍTICO              │
                         │                         │
                         │  ┌──────────────────┐   │
                         │  │ 1. INGESTA       │   │
                         │  │  • Pull 100% BD  │   │
                         │  │  • Export CSV    │   │
                         │  │  • Upload S3     │   │
                         │  │  • Catalog Glue  │   │
                         │  └──────────────────┘   │
                         │           │             │
                         │           ▼             │
                         │     Amazon S3           │
                         │     AWS Glue            │
                         │           │             │
                         │           ▼             │
                         │  ┌──────────────────┐   │
                         │  │ 2. API ANALÍTICA │   │
                         │  │  • FastAPI       │   │
                         │  │  • Pandas        │   │
                         │  │  • Queries S3    │   │
                         │  │  • Swagger UI    │   │
                         │  └──────────────────┘   │
                         │           │             │
                         │           ▼             │
                         │  ┌──────────────────┐   │
                         │  │ 3. LOAD BALANCER │   │
                         │  │  • Nginx         │   │
                         │  │  • 2 VMs Prod    │   │
                         │  └──────────────────┘   │
                         │                         │
                         └─────────────────────────┘
```

### Flujo de Datos

```
1. INGESTA (Una sola vez)
   MySQL/PostgreSQL/Cassandra → Contenedor Ingesta → S3 → AWS Glue Catalog

2. CONSULTAS (Continuas)
   Usuario → Nginx → API Analítica → Lee S3 → Procesa con Pandas → Retorna JSON
```

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.11**: Lenguaje principal
- **FastAPI**: Framework web para API REST
- **Uvicorn**: Servidor ASGI
- **Pandas**: Procesamiento y análisis de datos
- **Boto3**: SDK de AWS para Python

### Bases de Datos
- **MySQL 8.0**: Base de datos relacional
- **PostgreSQL 16**: Base de datos relacional avanzada
- **Cassandra 4.1**: Base de datos NoSQL distribuida

### Conectores de Bases de Datos
- **PyMySQL**: Conector MySQL
- **Psycopg2**: Conector PostgreSQL
- **Cassandra Driver**: Conector Cassandra

### AWS Services
- **Amazon S3**: Almacenamiento de datos
- **AWS Glue**: Catálogo de datos
- **AWS Athena**: Queries SQL sobre S3 (preparado para uso)

### DevOps
- **Docker**: Contenedorización
- **Docker Compose**: Orquestación de contenedores
- **Nginx**: Balanceador de carga
- **Git**: Control de versiones

---

## 📦 Requisitos Previos

### Software Necesario

- **Docker** (versión 20.10+)
- **Docker Compose** (versión 2.0+)
- **Git**
- **Cuenta AWS** con permisos para S3 y Glue

### Permisos IAM Requeridos en AWS

Tu usuario IAM debe tener los siguientes permisos:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::tu-bucket-name",
        "arn:aws:s3:::tu-bucket-name/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:CreateDatabase",
        "glue:GetDatabase",
        "glue:CreateTable",
        "glue:UpdateTable",
        "glue:GetTable"
      ],
      "Resource": "*"
    }
  ]
}
```

### Información Requerida de Compañeros (Solo para Producción)

Para desplegar en producción, necesitas que tus compañeros te proporcionen:

**Compañero con MySQL:**
- Host/IP de la base de datos
- Puerto (usualmente 3306)
- Usuario y contraseña
- Nombre de la base de datos

**Compañero con PostgreSQL:**
- Host/IP de la base de datos
- Puerto (usualmente 5432)
- Usuario y contraseña
- Nombre de la base de datos

**Compañero con Cassandra:**
- Host/IP de la base de datos
- Puerto (usualmente 9042)
- Keyspace

---

## ⚙️ Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd proyecto_parcial
```

### 2. Estructura de Archivos

```
proyecto_parcial/
├── docker-compose.yml              # Para desarrollo local
├── docker-compose.production.yml   # Para producción
├── .env.example                    # Variables de entorno para local
├── .env.production.example         # Variables de entorno para producción
├── orchestrator.py                 # Orquestador de servicios
├── services/
│   ├── data_science_api/          # API Analítica
│   │   ├── main.py                # Endpoints FastAPI
│   │   ├── s3_data_manager.py     # Gestor de datos S3
│   │   ├── mysql_s3_analytics.py  # Analytics MySQL
│   │   ├── postgresql_s3_analytics.py
│   │   ├── cassandra_s3_analytics.py
│   │   ├── cross_microservice_analytics.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── ingesta/                   # Servicio de Ingesta
│       ├── ingest_data.py         # Script de ingesta
│       ├── requirements.txt
│       └── Dockerfile
├── load_balancer/
│   └── nginx.conf                 # Configuración Nginx
└── README.md
```

---

## 🖥️ Modo Desarrollo Local

Este modo levanta TODAS las bases de datos localmente para pruebas.

### Paso 1: Configurar Variables de Entorno

```bash
cp .env.example .env
```

Edita el archivo `.env`:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=tu_access_key_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui
AWS_SESSION_TOKEN=tu_session_token_aqui  # Solo si usas AWS Academy
AWS_DEFAULT_REGION=us-east-1

# S3 Configuration
S3_BUCKET=tu-bucket-primac-analytics

# MySQL Configuration (Local)
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=primac
MYSQL_USER=admin
MYSQL_PASSWORD=admin
MYSQL_ROOT_PASSWORD=root

# PostgreSQL Configuration (Local)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=primac_postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Cassandra Configuration (Local)
CASSANDRA_HOST=cassandra
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=primac_keyspace

# Environment
ENVIRONMENT=local
```

### Paso 2: Crear Bucket S3

```bash
# Crear bucket en AWS
aws s3 mb s3://tu-bucket-primac-analytics --region us-east-1
```

### Paso 3: Levantar los Servicios

```bash
# Construir y levantar todos los contenedores
docker compose up --build

# O en modo detached (background)
docker compose up --build -d
```

Esto levantará:
- ✅ MySQL (puerto 3307)
- ✅ PostgreSQL (puerto 5432)
- ✅ Cassandra (puerto 9042)
- ✅ Servicio de Ingesta (ejecuta una vez)
- ✅ API Analítica (puerto 8000)
- ✅ Balanceador de carga (puerto 80)

### Paso 4: Verificar Servicios

```bash
# Ver estado de contenedores
docker compose ps

# Ver logs
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f analytics_api
```

### Paso 5: Acceder a la API

Abre tu navegador en:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **A través del balanceador**: http://localhost/docs

### Paso 6: Probar Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Estadísticas de usuarios MySQL
curl http://localhost:8000/mysql/analytics/users

# Análisis de productos PostgreSQL
curl http://localhost:8000/postgresql/analytics/products

# Análisis de reclamos Cassandra
curl http://localhost:8000/cassandra/analytics/claims
```

### Detener Servicios Locales

```bash
# Detener contenedores
docker compose down

# Detener y eliminar volúmenes (limpieza completa)
docker compose down -v
```

---

## 🚀 Modo Producción

Este modo se conecta a las bases de datos remotas de tus compañeros.

### Arquitectura de Producción

```
VM Compañero A → MySQL BD
VM Compañero B → PostgreSQL BD
VM Compañero C → Cassandra BD
                    ↓
         TU VM 1 ← Ingesta → S3 + Glue
         TU VM 2 ← API Analítica
                    ↓
         Application Load Balancer (AWS)
```

### Paso 1: Recopilar Información de Compañeros

Crea un documento con esta información:

```
=== MICROSERVICIO MYSQL ===
Host: _________________________________
Puerto: _______________________________
Usuario: ______________________________
Password: _____________________________
Database: _____________________________

=== MICROSERVICIO POSTGRESQL ===
Host: _________________________________
Puerto: _______________________________
Usuario: ______________________________
Password: _____________________________
Database: _____________________________

=== MICROSERVICIO CASSANDRA ===
Host: _________________________________
Puerto: _______________________________
Keyspace: _____________________________
```

### Paso 2: Configurar Security Groups

**IMPORTANTE**: Tus compañeros deben permitir conexiones desde tu EC2.

Cada compañero debe agregar en sus Security Groups:

```
MySQL:
Tipo: MySQL/Aurora
Puerto: 3306
Origen: <IP_DE_TU_EC2>/32

PostgreSQL:
Tipo: PostgreSQL
Puerto: 5432
Origen: <IP_DE_TU_EC2>/32

Cassandra:
Tipo: Custom TCP
Puerto: 9042
Origen: <IP_DE_TU_EC2>/32
```

### Paso 3: Configurar Variables de Entorno

```bash
cp .env.production.example .env.production
nano .env.production
```

Completa con los datos reales:

```env
# AWS Configuration (TU CUENTA)
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_SESSION_TOKEN=tu_session_token
AWS_DEFAULT_REGION=us-east-1

# S3 Configuration (TU BUCKET)
S3_BUCKET=tu-bucket-primac-analytics

# MySQL REMOTO (Datos del Compañero A)
MYSQL_HOST_REMOTE=ec2-xx-xxx-xxx-xx.compute-1.amazonaws.com
MYSQL_PORT_REMOTE=3306
MYSQL_USER_REMOTE=usuario_companero
MYSQL_PASSWORD_REMOTE=password_companero
MYSQL_DATABASE_REMOTE=database_companero

# PostgreSQL REMOTO (Datos del Compañero B)
POSTGRES_HOST_REMOTE=ec2-yy-yyy-yyy-yy.compute-1.amazonaws.com
POSTGRES_PORT_REMOTE=5432
POSTGRES_USER_REMOTE=usuario_companero
POSTGRES_PASSWORD_REMOTE=password_companero
POSTGRES_DB_REMOTE=database_companero

# Cassandra REMOTO (Datos del Compañero C)
CASSANDRA_HOST_REMOTE=ec2-zz-zzz-zzz-zz.compute-1.amazonaws.com
CASSANDRA_PORT_REMOTE=9042
CASSANDRA_KEYSPACE_REMOTE=keyspace_companero

# Environment
ENVIRONMENT=production
```

### Paso 4: Crear y Configurar EC2

#### 4.1. Crear Instancia EC2

En AWS Console:
1. Launch Instance
2. **AMI**: Ubuntu Server 22.04 LTS
3. **Instance type**: t2.medium (mínimo)
4. **Security Group**: Permitir puertos 22, 80, 8000
5. **Storage**: 20 GB mínimo

#### 4.2. Conectar a la EC2

```bash
ssh -i tu-key.pem ubuntu@tu-ec2-public-ip
```

#### 4.3. Instalar Docker y Docker Compose

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Salir y volver a conectar para aplicar cambios
exit
ssh -i tu-key.pem ubuntu@tu-ec2-public-ip
```

#### 4.4. Verificar Instalación

```bash
docker --version
docker-compose --version
```

### Paso 5: Desplegar el Proyecto

```bash
# Clonar repositorio
git clone <url-repositorio>
cd proyecto_parcial

# Copiar y configurar variables de entorno
cp .env.production.example .env.production
nano .env.production  # Editar con datos reales

# Levantar servicios en producción
docker-compose -f docker-compose.production.yml up --build -d
```

### Paso 6: Ejecutar Ingesta Inicial

```bash
# Ejecutar proceso de ingesta (solo una vez)
docker-compose -f docker-compose.production.yml run --rm ingesta

# Monitorear logs
docker-compose -f docker-compose.production.yml logs -f ingesta
```

La ingesta hará:
1. ✅ Conectarse a las 3 bases de datos remotas
2. ✅ Extraer el 100% de los registros
3. ✅ Convertir a CSV
4. ✅ Subir a S3
5. ✅ Crear catálogo en AWS Glue (`primac_analytics_db`)

### Paso 7: Verificar Despliegue

#### 7.1. Verificar Contenedores

```bash
docker-compose -f docker-compose.production.yml ps
```

Deberías ver:
- `analytics_api_production` (running)
- `nginx_lb_production` (running)

#### 7.2. Verificar S3

```bash
aws s3 ls s3://tu-bucket-primac-analytics/ --recursive
```

Deberías ver archivos como:
```
mysql/users/users.csv
mysql/clients/clients.csv
postgres/products/products.csv
postgres/policies/policies.csv
cassandra/reclamos/reclamos.csv
cassandra/pagos/pagos.csv
```

#### 7.3. Verificar AWS Glue

En AWS Console → Glue → Databases:
- Database: `primac_analytics_db`
- Tables: `mysql_users`, `postgresql_products`, `cassandra_reclamos`, etc.

#### 7.4. Probar API

```bash
# Health check
curl http://tu-ec2-public-ip:8000/health

# Swagger UI
http://tu-ec2-public-ip:8000/docs
```

### Paso 8: Configurar 2da VM y Load Balancer (Opcional)

Para producción real con alta disponibilidad:

#### 8.1. Repetir pasos 4-7 en una segunda EC2

#### 8.2. Crear Application Load Balancer

En AWS Console:
1. EC2 → Load Balancers → Create Application Load Balancer
2. **Listeners**: HTTP (80), HTTPS (443)
3. **Target Group**:
   - Protocol: HTTP
   - Port: 8000
   - Health check path: `/health`
4. **Targets**: Agregar ambas EC2
5. Obtener DNS del Load Balancer

Acceder vía: `http://tu-load-balancer-dns.amazonaws.com/docs`

### Comandos Útiles en Producción

```bash
# Ver logs
docker-compose -f docker-compose.production.yml logs -f

# Reiniciar API
docker-compose -f docker-compose.production.yml restart analytics_api

# Detener todo
docker-compose -f docker-compose.production.yml down

# Ver uso de recursos
docker stats

# Limpiar espacio
docker system prune -a
```

---

## 📡 Endpoints de la API

Una vez desplegada, la API expone los siguientes endpoints:

### 🏥 Health Checks

#### `GET /`
**Información general de la API**

```bash
curl http://localhost:8000/
```

Respuesta:
```json
{
  "message": "API Analytics - Primac S3",
  "version": "2.0.0",
  "status": "OK",
  "data_source": "S3 Bucket",
  "available_databases": ["MySQL", "PostgreSQL", "Cassandra"],
  "endpoints": {
    "mysql": 2,
    "postgresql": 2,
    "cassandra": 2,
    "cross_microservice": 3
  }
}
```

#### `GET /health`
**Estado del servicio y disponibilidad de datos en S3**

```bash
curl http://localhost:8000/health
```

Respuesta:
```json
{
  "status": "OK",
  "timestamp": "2025-10-22T10:30:00",
  "data_availability": {
    "mysql": {
      "users": true,
      "clients": true,
      "agents": true
    },
    "postgresql": {
      "products": true,
      "policies": true
    },
    "cassandra": {
      "reclamos": true,
      "pagos": true
    }
  },
  "bucket_summary": {
    "total_objects": 12,
    "total_size_mb": 45.67
  }
}
```

### 🗄️ MySQL Analytics

#### `GET /mysql/analytics/users`
**Estadísticas generales de usuarios**

Analiza datos de la tabla `users` de MySQL.

```bash
curl http://localhost:8000/mysql/analytics/users
```

Retorna:
- Total de usuarios registrados
- Distribución por estado/región
- Estadísticas demográficas
- Análisis temporal de registros

#### `GET /mysql/analytics/growth-by-state?months=12`
**Crecimiento de usuarios por estado**

Analiza evolución temporal del registro de usuarios.

```bash
curl "http://localhost:8000/mysql/analytics/growth-by-state?months=12"
```

Parámetros:
- `months` (opcional): Ventana temporal en meses (1-36), default: 12

Retorna:
- Serie temporal de registros por estado
- Tasa de crecimiento por región
- Estados con mayor crecimiento

### 🗄️ PostgreSQL Analytics

#### `GET /postgresql/analytics/products`
**Análisis completo de productos y pólizas**

Analiza datos de las tablas `products` y `policies` de PostgreSQL.

```bash
curl http://localhost:8000/postgresql/analytics/products
```

Retorna:
- Total de productos disponibles
- Distribución de pólizas por tipo
- Estadísticas de cobertura
- Productos más vendidos

#### `GET /postgresql/analytics/product-profitability`
**Análisis de rentabilidad por producto**

```bash
curl http://localhost:8000/postgresql/analytics/product-profitability
```

Retorna:
- Ingresos por producto
- Número de pólizas activas
- Valor promedio de primas
- ROI y métricas de rentabilidad

### 🗄️ Cassandra Analytics

#### `GET /cassandra/analytics/claims`
**Análisis de reclamos y siniestros**

Analiza datos de la tabla `reclamos` de Cassandra.

```bash
curl http://localhost:8000/cassandra/analytics/claims
```

Retorna:
- Total de reclamos registrados
- Distribución por tipo de reclamo
- Estados (pendiente, aprobado, rechazado)
- Montos promedio de reclamos

#### `GET /cassandra/analytics/claims-payments-correlation`
**Correlación entre reclamos y pagos**

```bash
curl http://localhost:8000/cassandra/analytics/claims-payments-correlation
```

Retorna:
- Tasa de aprobación de reclamos
- Tiempo promedio entre reclamo y pago
- Monto promedio pagado vs reclamado
- Eficiencia del proceso

### 🔄 Cross-Microservice Analytics

#### `GET /cross/analytics/customer-policy-profile`
**Perfil de clientes y sus pólizas** (MySQL + PostgreSQL)

Combina datos de clientes (MySQL) con sus pólizas (PostgreSQL).

```bash
curl http://localhost:8000/cross/analytics/customer-policy-profile
```

Retorna:
- Perfil demográfico de clientes
- Pólizas activas por cliente
- Valor total de cobertura
- Segmentación de clientes

#### `GET /cross/analytics/agent-performance`
**Rendimiento de agentes de ventas** (MySQL + PostgreSQL)

Combina datos de agentes (MySQL) con pólizas vendidas (PostgreSQL).

```bash
curl http://localhost:8000/cross/analytics/agent-performance
```

Retorna:
- Pólizas vendidas por agente
- Valor total de primas generadas
- Ranking de agentes
- Tasa de conversión

#### `GET /cross/analytics/claims-vs-policies`
**Análisis de siniestralidad** (PostgreSQL + Cassandra)

Combina pólizas (PostgreSQL) con reclamos (Cassandra).

```bash
curl http://localhost:8000/cross/analytics/claims-vs-policies
```

Retorna:
- Ratio de siniestralidad por producto
- Frecuencia de reclamos
- Loss ratio (pagos/primas)
- Productos con mayor/menor siniestralidad

---

## 📂 Estructura del Proyecto

```
proyecto_parcial/
│
├── services/
│   ├── data_science_api/              # API de Análisis
│   │   ├── main.py                    # Endpoints FastAPI con Swagger
│   │   ├── s3_data_manager.py         # Gestor de datos desde S3
│   │   ├── mysql_s3_analytics.py      # Lógica de analytics MySQL
│   │   ├── postgresql_s3_analytics.py # Lógica de analytics PostgreSQL
│   │   ├── cassandra_s3_analytics.py  # Lógica de analytics Cassandra
│   │   ├── cross_microservice_analytics.py  # Analytics cruzados
│   │   ├── requirements.txt           # Dependencias Python
│   │   └── Dockerfile                 # Container de la API
│   │
│   └── ingesta/                       # Servicio de Ingesta
│       ├── ingest_data.py             # Script de ingesta a S3 + Glue
│       ├── requirements.txt           # Dependencias Python
│       └── Dockerfile                 # Container de ingesta
│
├── load_balancer/
│   └── nginx.conf                     # Configuración del Load Balancer
│
├── docker-compose.yml                 # Orquestación para desarrollo local
├── docker-compose.production.yml      # Orquestación para producción
├── orchestrator.py                    # Script orquestador de servicios
│
├── .env.example                       # Template variables locales
├── .env.production.example            # Template variables producción
└── README.md                          # Este archivo (guía completa)
```

### Descripción de Componentes Clave

**`services/data_science_api/main.py`**
- Define todos los endpoints REST
- Documentación Swagger/OpenAPI
- Manejo de errores y validaciones

**`services/ingesta/ingest_data.py`**
- Conexión a las 3 bases de datos
- Extracción completa de datos (100%)
- Upload a S3
- Creación de catálogo en AWS Glue

**`docker-compose.yml`**
- Levanta bases de datos locales (MySQL, PostgreSQL, Cassandra)
- Para desarrollo y pruebas locales

**`docker-compose.production.yml`**
- No levanta bases de datos
- Se conecta a bases remotas de compañeros
- Para despliegue en producción

---

## 🔧 Troubleshooting

### Problema: No puedo conectarme a las bases de datos remotas

**Síntomas:**
```
Error: Can't connect to MySQL server
Error: Connection refused PostgreSQL
```

**Soluciones:**

1. **Verificar Security Groups**
   - Los Security Groups de tus compañeros deben permitir tu IP en los puertos correctos
   - Verificar con: `telnet host-remoto puerto`

2. **Verificar credenciales**
   - Confirmar usuario y password con tus compañeros
   - Verificar que el usuario tenga permisos de lectura

3. **Probar conexión manualmente**
   ```bash
   # MySQL
   mysql -h host-remoto -u usuario -p

   # PostgreSQL
   psql -h host-remoto -U usuario -d database

   # Cassandra
   cqlsh host-remoto 9042
   ```

### Problema: Error de permisos en AWS S3/Glue

**Síntomas:**
```
AccessDenied: User is not authorized to perform: s3:PutObject
AccessDenied: User is not authorized to perform: glue:CreateTable
```

**Soluciones:**

1. **Verificar permisos IAM**
   - Tu usuario debe tener permisos `s3:PutObject`, `s3:GetObject`
   - Tu usuario debe tener permisos `glue:CreateDatabase`, `glue:CreateTable`

2. **Si usas AWS Academy**
   - El `AWS_SESSION_TOKEN` expira cada 4 horas
   - Regenerar credenciales desde AWS Academy
   - Actualizar `.env` o `.env.production`

3. **Verificar bucket existe**
   ```bash
   aws s3 ls s3://tu-bucket-primac-analytics/
   ```

### Problema: La ingesta tarda mucho o falla

**Síntomas:**
```
Timeout waiting for connection
Process killed (OOM)
```

**Soluciones:**

1. **Verificar volumen de datos**
   - Es normal que tarde varios minutos con 20,000+ registros
   - Monitorear con: `docker logs -f ingesta`

2. **Aumentar recursos de Docker**
   - Docker Desktop → Settings → Resources
   - Aumentar RAM a 4GB mínimo

3. **Verificar timeouts de red**
   - Bases de datos remotas pueden tener timeouts cortos
   - Contactar a compañeros para aumentar `wait_timeout` (MySQL) o `statement_timeout` (PostgreSQL)

### Problema: La API no responde

**Síntomas:**
```
curl: (7) Failed to connect to localhost port 8000
```

**Soluciones:**

1. **Verificar contenedor corriendo**
   ```bash
   docker ps | grep analytics_api
   ```

2. **Ver logs del contenedor**
   ```bash
   docker logs analytics_api
   ```

3. **Verificar puerto no ocupado**
   ```bash
   sudo lsof -i :8000
   ```

4. **Reiniciar contenedor**
   ```bash
   docker-compose restart analytics_api
   ```

### Problema: Swagger UI no muestra la documentación

**Síntomas:**
- Página en blanco en `/docs`
- Error 404

**Soluciones:**

1. **Verificar que la API esté corriendo**
   ```bash
   curl http://localhost:8000/
   ```

2. **Limpiar cache del navegador**
   - Ctrl + Shift + R (forzar recarga)

3. **Probar con `/redoc` alternativo**
   ```
   http://localhost:8000/redoc
   ```

### Problema: Datos no aparecen en S3

**Síntomas:**
- Bucket vacío después de ingesta
- Error al listar archivos

**Soluciones:**

1. **Verificar logs de ingesta**
   ```bash
   docker logs ingesta
   ```

2. **Verificar bucket correcto**
   ```bash
   aws s3 ls  # Lista todos tus buckets
   ```

3. **Verificar permisos de escritura**
   ```bash
   aws s3 cp test.txt s3://tu-bucket-primac-analytics/test.txt
   ```

### Problema: AWS Glue Catalog no se crea

**Síntomas:**
- Database `primac_analytics_db` no aparece en Glue Console
- Tablas no visibles

**Soluciones:**

1. **Verificar región correcta**
   - AWS Console debe estar en la misma región que `AWS_DEFAULT_REGION` en `.env`

2. **Verificar permisos Glue**
   ```bash
   aws glue get-databases
   ```

3. **Ejecutar ingesta nuevamente**
   ```bash
   docker-compose -f docker-compose.production.yml run --rm ingesta
   ```

### Problema: Out of Memory en EC2

**Síntomas:**
```
Killed
Process terminated (137)
```

**Soluciones:**

1. **Verificar recursos de EC2**
   ```bash
   free -h
   htop
   ```

2. **Usar instancia más grande**
   - Mínimo recomendado: t2.medium (4GB RAM)
   - Para producción: t2.large o t3.large

3. **Agregar swap space**
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

---

## 📞 Soporte y Contacto

### Recursos Adicionales

- **Documentación FastAPI**: https://fastapi.tiangolo.com/
- **Documentación Boto3**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **Documentación AWS Glue**: https://docs.aws.amazon.com/glue/
- **Docker Compose**: https://docs.docker.com/compose/

### Checklist de Despliegue

#### Antes del Despliegue:
- [ ] Recopilar credenciales de bases de datos de compañeros
- [ ] Configurar Security Groups para permitir conexiones
- [ ] Crear bucket S3 en AWS
- [ ] Verificar permisos IAM (S3 + Glue)
- [ ] Probar conexiones a bases de datos remotas

#### Durante el Despliegue:
- [ ] Crear EC2 instance con puertos 22, 80, 8000 abiertos
- [ ] Instalar Docker y Docker Compose en EC2
- [ ] Clonar repositorio
- [ ] Configurar `.env.production` con datos reales
- [ ] Ejecutar `docker-compose.production.yml`
- [ ] Ejecutar ingesta de datos

#### Después del Despliegue:
- [ ] Verificar datos en S3
- [ ] Verificar catálogo en AWS Glue
- [ ] Probar todos los endpoints de la API
- [ ] Verificar Swagger UI accesible
- [ ] Compartir URL de tu API con el equipo

---

## 📄 Licencia

Este proyecto es parte de un trabajo académico para el curso de Cloud Computing - UTEC.

---

## 🙏 Agradecimientos

- Equipo de desarrollo Primac
- Profesores del curso Cloud Computing
- Compañeros de equipo por sus microservicios

---

**Versión**: 2.0.0
**Última actualización**: Octubre 2025
**Autor**: Equipo Analítica Primac
