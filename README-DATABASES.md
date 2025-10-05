# Primac Databases Docker Compose Setup

This Docker Compose configuration binds all three databases used in the Primac project:

## 🗄️ Databases Included

1. **MySQL** (BD_Users_Primac) - Port 3307
2. **PostgreSQL** - Port 5432
3. **Cassandra** (Primac-Claims-Payments-DB) - Port 9042

## 🚀 Quick Start

### 1. Set up environment variables
```bash
cp .env.example .env
# Edit .env file with your actual AWS credentials and other settings
```

### 2. Start all services
```bash
# Start all databases and services
docker compose up -d

# Or start specific services
docker compose up -d mysql-db postgresql-db cassandra-db
```

### 3. Initialize Cassandra (if needed)
```bash
# Run Cassandra setup to create keyspace and tables
docker compose up cassandra-setup
```

## 📊 Service Endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| **MySQL** | `localhost:3307` | admin/admin |
| **PostgreSQL** | `localhost:5432` | postgres/postgres |
| **Cassandra** | `localhost:9042` | - |
| **Data Science API** | `http://localhost:8000` | - |
| **PostgreSQL API** | `http://localhost:8001` | - |
| **Adminer** (DB Manager) | `http://localhost:8081` | - |
| **pgAdmin** | `http://localhost:8082` | admin@admin.com/admin |

## 🛠️ Management Commands

### Start specific database
```bash
# Start only MySQL
docker compose up -d mysql-db

# Start only PostgreSQL
docker compose up -d postgresql-db postgresql-api

# Start only Cassandra
docker compose up -d cassandra-db cassandra-setup
```

### View logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f mysql-db
docker compose logs -f postgresql-db
docker compose logs -f cassandra-db
```

### Stop services
```bash
# Stop all
docker compose down

# Stop and remove volumes (⚠️ This will delete all data)
docker compose down -v
```

### Database connections from applications

#### MySQL Connection
```
Host: mysql-db (or localhost from host machine)
Port: 3307 (3306 from within Docker network)
Database: primac
User: admin
Password: admin
```

#### PostgreSQL Connection
```
Host: postgresql-db (or localhost from host machine)
Port: 5432
Database: primac_postgres
User: postgres
Password: postgres
```

#### Cassandra Connection
```
Host: cassandra-db (or localhost from host machine)
Port: 9042
Keyspace: primac_db (after setup)
```

## 📁 Project Structure

```
proyecto_parcial/
├── databases/
│   ├── BD_Users_Primac/          # MySQL database
│   ├── proyecto_postgresql/       # PostgreSQL API
│   └── Primac-Claims-Payments-DB/ # Cassandra database
├── services/
│   └── data_science_api/         # Data Science API
├── docker-compose.yml            # Main compose file
├── .env.example                  # Environment template
└── README-DATABASES.md           # This file
```

## 🔧 Troubleshooting

### Database not starting
1. Check logs: `docker compose logs [service-name]`
2. Ensure ports are not in use: `netstat -tlnp | grep [port]`
3. Remove volumes and restart: `docker compose down -v && docker compose up -d`

### Cassandra setup issues
1. Wait for Cassandra to be fully ready (can take 2-3 minutes)
2. Run setup manually: `docker compose up cassandra-setup`
3. Check if scripts exist in `databases/Primac-Claims-Payments-DB/docker/scripts/`

### Connection issues
- From applications within Docker network: use service names (e.g., `mysql-db`, `postgresql-db`, `cassandra-db`)
- From host machine: use `localhost` with mapped ports

## 🌐 Network Configuration

All services run on the `primac_network` with subnet `172.20.0.0/16`. Services can communicate with each other using their container names.

## 💾 Data Persistence

Data is persisted using named volumes:
- `mysql_data` - MySQL data
- `postgresql_data` - PostgreSQL data  
- `cassandra_data` - Cassandra data
- `pgadmin_data` - pgAdmin settings

## ⚡ Performance Tips

1. **For development**: Use `docker compose up` to see logs in real-time
2. **For production**: Use `docker compose up -d` to run in background
3. **Resource allocation**: Adjust memory limits in compose file if needed
4. **Health checks**: All databases have health checks for better dependency management