# Configuración Docker Compose - Bases de Datos Primac

Esta configuración de Docker Compose conecta las tres bases de datos utilizadas en el proyecto Primac:

## 🗄️ Bases de Datos Incluidas

1. **MySQL** (BD_Users_Primac) - Puerto 3307
2. **PostgreSQL** - Puerto 5432
3. **Cassandra** (Primac-Claims-Payments-DB) - Puerto 9042

## 🚀 Inicio Rápido

### 1. Configurar variables de entorno
```bash
cp .env.example .env
# Edita el archivo .env con tus credenciales de AWS y otras configuraciones
```

### 2. Iniciar todos los servicios
```bash
# Iniciar todas las bases de datos y servicios
docker compose up -d

# O iniciar servicios específicos
docker compose up -d mysql-db postgresql-db cassandra-db
```

### 3. Inicializar Cassandra (si es necesario)
```bash
# Ejecutar configuración de Cassandra para crear keyspace y tablas
docker compose up cassandra-setup
```

## 📊 Endpoints de Servicios

| Servicio | URL | Credenciales |
|----------|-----|-------------|
| **MySQL** | `localhost:3307` | admin/admin |
| **PostgreSQL** | `localhost:5432` | postgres/postgres |
| **Cassandra** | `localhost:9042` | - |
| **API Data Science** | `http://localhost:8000` | - |
| **API PostgreSQL** | `http://localhost:8001` | - |
| **Adminer** (Gestor BD) | `http://localhost:8081` | - |
| **pgAdmin** | `http://localhost:8082` | admin@admin.com/admin |

## 🛠️ Comandos de Gestión

### Iniciar base de datos específica
```bash
# Iniciar solo MySQL
docker compose up -d mysql-db

# Iniciar solo PostgreSQL
docker compose up -d postgresql-db postgresql-api

# Iniciar solo Cassandra
docker compose up -d cassandra-db cassandra-setup
```

### Ver logs
```bash
# Todos los servicios
docker compose logs -f

# Servicio específico
docker compose logs -f mysql-db
docker compose logs -f postgresql-db
docker compose logs -f cassandra-db
```

### Detener servicios
```bash
# Detener todo
docker compose down

# Detener y eliminar volúmenes (⚠️ Esto eliminará todos los datos)
docker compose down -v
```

### Conexiones a bases de datos desde aplicaciones

#### Conexión MySQL
```
Host: mysql-db (o localhost desde máquina host)
Puerto: 3307 (3306 desde red Docker interna)
Base de datos: primac
Usuario: admin
Contraseña: admin
```

#### Conexión PostgreSQL
```
Host: postgresql-db (o localhost desde máquina host)
Puerto: 5432
Base de datos: primac_postgres
Usuario: postgres
Contraseña: postgres
```

#### Conexión Cassandra
```
Host: cassandra-db (o localhost desde máquina host)
Puerto: 9042
Keyspace: primac_db (después de la configuración)
```

## 📁 Estructura del Proyecto

```
proyecto_parcial/
├── databases/
│   ├── BD_Users_Primac/          # Base de datos MySQL
│   ├── proyecto_postgresql/       # API PostgreSQL
│   └── Primac-Claims-Payments-DB/ # Base de datos Cassandra
├── services/
│   └── data_science_api/         # API Data Science
├── docker-compose.yml            # Archivo compose principal
├── .env.example                  # Plantilla de entorno
└── README-BASES-DATOS.md         # Este archivo
```

## 🔧 Solución de Problemas

### Base de datos no inicia
1. Revisar logs: `docker compose logs [nombre-servicio]`
2. Asegurar que los puertos no estén en uso: `netstat -tlnp | grep [puerto]`
3. Eliminar volúmenes y reiniciar: `docker compose down -v && docker compose up -d`

### Problemas con configuración de Cassandra
1. Esperar a que Cassandra esté completamente listo (puede tomar 2-3 minutos)
2. Ejecutar configuración manualmente: `docker compose up cassandra-setup`
3. Verificar que existan los scripts en `databases/Primac-Claims-Payments-DB/docker/scripts/`

### Problemas de conexión
- Desde aplicaciones dentro de la red Docker: usar nombres de servicio (ej: `mysql-db`, `postgresql-db`, `cassandra-db`)
- Desde máquina host: usar `localhost` con puertos mapeados

## 🌐 Configuración de Red

Todos los servicios corren en la red `primac_network` con subnet `172.20.0.0/16`. Los servicios pueden comunicarse entre sí usando sus nombres de contenedor.

## 💾 Persistencia de Datos

Los datos se persisten usando volúmenes nombrados:
- `mysql_data` - Datos MySQL
- `postgresql_data` - Datos PostgreSQL  
- `cassandra_data` - Datos Cassandra
- `pgadmin_data` - Configuraciones pgAdmin

## ⚡ Consejos de Rendimiento

1. **Para desarrollo**: Usar `docker compose up` para ver logs en tiempo real
2. **Para producción**: Usar `docker compose up -d` para ejecutar en segundo plano
3. **Asignación de recursos**: Ajustar límites de memoria en el archivo compose si es necesario
4. **Health checks**: Todas las bases de datos tienen verificaciones de salud para mejor gestión de dependencias

## 🔐 Seguridad

⚠️ **IMPORTANTE**: Las credenciales mostradas son para desarrollo. En producción:
- Cambiar todas las contraseñas por defecto
- Usar variables de entorno seguras
- Configurar acceso restringido a puertos
- Implementar SSL/TLS para conexiones

## 📝 Comandos Útiles Adicionales

### Hacer backup de bases de datos
```bash
# Backup MySQL
docker exec primac_mysql_db mysqldump -u admin -padmin primac > backup_mysql.sql

# Backup PostgreSQL
docker exec primac_postgresql_db pg_dump -U postgres primac_postgres > backup_postgres.sql

# Backup Cassandra (keyspace completo)
docker exec primac_cassandra_db cqlsh -e "DESCRIBE primac_db;" > backup_cassandra.cql
```

### Restaurar bases de datos
```bash
# Restaurar MySQL
docker exec -i primac_mysql_db mysql -u admin -padmin primac < backup_mysql.sql

# Restaurar PostgreSQL
docker exec -i primac_postgresql_db psql -U postgres -d primac_postgres < backup_postgres.sql

# Restaurar Cassandra
docker exec -i primac_cassandra_db cqlsh < backup_cassandra.cql
```

### Monitoreo de recursos
```bash
# Ver uso de recursos por contenedor
docker stats

# Ver espacio usado por volúmenes
docker system df -v

# Limpiar recursos no utilizados
docker system prune -a
```

## 🆘 Contacto y Soporte

Si encuentras problemas:
1. Revisa la sección de solución de problemas
2. Consulta los logs de los servicios
3. Verifica que todos los archivos de configuración estén presentes
4. Asegúrate de que Docker y Docker Compose estén actualizados