# Docker Setup Guide

This guide explains how to run the PracticePython FastAPI application using Docker and Docker Compose, following security best practices.

## 🐳 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB RAM available

### 1. Environment Setup

The Docker setup uses sensible defaults and doesn't require a separate environment file. All required settings are configured in `docker-compose.yml` with fallback values.

**⚠️ OPTIONAL: Override default values by setting environment variables:**
- `POSTGRES_PASSWORD` - Database password (default: `secure_local_password`)
- `SECRET_KEY` - JWT secret (default: development key)
- `FIRST_PASSWORD` - Admin password (default: `admin_password_123`)

```bash
# Example with custom values
export POSTGRES_PASSWORD=my_secure_password
export SECRET_KEY=my_32_character_secret_key_here
export FIRST_PASSWORD=my_admin_password
```

### 2. Production Deployment

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 3. Development Mode

The default setup is already configured for development:

```bash
# Start all services
docker-compose up -d

# View logs during development
docker-compose logs -f app
```

## 🏗️ Architecture

### Services

| Service | Purpose | Port | Health Check |
|---------|---------|------|--------------|
| **app** | FastAPI application | 8000 | `/health` |
| **postgres** | PostgreSQL database | 5432 | `pg_isready` |
| **redis** | Redis cache | 6379 | `redis-cli ping` |
| **migrate** | Database setup (init container) | - | Runs once |

### Database Access

You can access the database directly using:

```bash
# PostgreSQL shell
docker-compose exec postgres psql -U appuser -d practicepython

# Redis CLI
docker-compose exec redis redis-cli
```

## 🔒 Security Features

### Container Security
- **Non-root execution**: All containers run as non-root users
- **Multi-stage builds**: Minimal production images
- **Read-only filesystems**: Source code mounted read-only in dev
- **Network isolation**: Custom bridge network
- **Health checks**: Comprehensive service monitoring

### Database Security
- **SCRAM-SHA-256 authentication**: Modern password hashing
- **Isolated network**: No direct external access in production
- **Persistent volumes**: Data survives container restarts

### Application Security
- **Environment-based configuration**: No hardcoded secrets
- **JWT token authentication**: Secure API access
- **CORS configuration**: Controlled cross-origin access
- **Rate limiting**: Built-in request throttling

## 📋 Management Commands

### Application Management

```bash
# View application logs
docker-compose logs -f app

# Access application shell
docker-compose exec app bash

# Run database migrations
docker-compose exec app alembic upgrade head

# Seed database manually
docker-compose exec app python scripts/seed_data.py

# Run tests
docker-compose exec app pytest
```

### Database Management

```bash
# Access PostgreSQL shell
docker-compose exec postgres psql -U appuser -d practicepython

# Create database backup
docker-compose exec postgres pg_dump -U appuser practicepython > backup.sql

# Restore database backup
docker-compose exec -T postgres psql -U appuser -d practicepython < backup.sql

# View database logs
docker-compose logs postgres
```

### Redis Management

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Monitor Redis commands
docker-compose exec redis redis-cli monitor

# View Redis logs
docker-compose logs redis
```

## 🚀 Deployment Scenarios

### Local Development

```bash
# Start all services
docker-compose up -d

# Access services
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

### Production Deployment

```bash
# Production deployment
docker-compose up -d

# Scale application (if needed)
docker-compose up -d --scale app=3

# Update application
docker-compose pull
docker-compose up -d --no-deps app
```

### CI/CD Pipeline

```bash
# Build and test
docker-compose build
docker-compose run --rm app pytest

# Deploy
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | PracticePython | Application name |
| `ENVIRONMENT` | production | Runtime environment |
| `SECRET_KEY` | *required* | JWT signing secret |
| `POSTGRES_PASSWORD` | *required* | Database password |
| `FIRST_USERNAME` | admin | Initial admin username |
| `FIRST_PASSWORD` | *required* | Initial admin password |
| `BACKEND_CORS_ORIGINS` | - | Allowed CORS origins |

### Volume Mounts

| Volume | Purpose | Persistence |
|--------|---------|-------------|
| `postgres_data` | Database files | Persistent |
| `redis_data` | Redis snapshots | Persistent |
| `./app` (dev) | Source code | Host-mounted |

## 🔍 Monitoring & Debugging

### Health Checks

```bash
# Check all service health
docker-compose ps

# Application health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready -U appuser
```

### Performance Monitoring

```bash
# Resource usage
docker stats

# Container resource limits
docker-compose exec app cat /sys/fs/cgroup/memory/memory.limit_in_bytes
```

### Log Analysis

```bash
# Follow all logs
docker-compose logs -f

# Application logs only
docker-compose logs -f app

# Error logs
docker-compose logs app | grep ERROR
```

## 🛠️ Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check PostgreSQL is running
docker-compose exec postgres pg_isready -U appuser

# Verify network connectivity
docker-compose exec app ping postgres
```

**Permission Denied**
```bash
# Check file ownership
ls -la app/

# Fix permissions (if needed)
sudo chown -R $USER:$USER app/
```

**Container Won't Start**
```bash
# Check container logs
docker-compose logs <service-name>

# Inspect container
docker-compose exec <service-name> bash
```

### Performance Issues

**Slow Database Queries**
```bash
# Enable query logging
docker-compose exec postgres psql -U appuser -d practicepython -c "ALTER SYSTEM SET log_statement = 'all';"
```

**Memory Issues**
```bash
# Check memory usage
docker stats

# Restart services
docker-compose restart
```

## 📚 Best Practices

### Security Checklist
- [ ] Change default passwords
- [ ] Use strong SECRET_KEY
- [ ] Configure CORS properly
- [ ] Enable HTTPS in production
- [ ] Regular security updates
- [ ] Monitor container logs

### Performance Optimization
- [ ] Use multi-stage builds
- [ ] Optimize Docker images
- [ ] Configure resource limits
- [ ] Use Redis for caching
- [ ] Monitor application metrics

### Maintenance
- [ ] Regular backups
- [ ] Log rotation
- [ ] Container updates
- [ ] Database maintenance
- [ ] Security scanning

## 📖 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Docker Guide](https://hub.docker.com/_/postgres)
- [Redis Docker Guide](https://hub.docker.com/_/redis)

---

For support or questions, please refer to the main project documentation or open an issue. 