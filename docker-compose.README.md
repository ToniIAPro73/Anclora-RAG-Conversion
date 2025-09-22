# Docker Compose Configuration - Anclora RAG

This document explains the improvements made to the `docker-compose.yml` configuration for the Anclora RAG system.

## 🚀 Key Improvements

### 1. **Updated Docker Compose Version**

- **Before**: `version: '3.6'` (2018)
- **After**: `version: '3.8'` (latest stable)
- **Benefits**: Better performance, security, and feature support

### 2. **Comprehensive Documentation**

- Added detailed header comments explaining the system architecture
- Service-specific documentation blocks for each component
- Clear separation of concerns with visual dividers

### 3. **Resource Management**

- **CPU Limits**: Set appropriate limits for each service (0.25-4.0 CPUs)
- **Memory Limits**: Configured memory constraints (256MB-8GB)
- **GPU Support**: Proper NVIDIA GPU resource allocation for Ollama
- **Benefits**: Prevents resource starvation, improves stability

### 4. **Restart Policies**

- **Policy**: `restart: unless-stopped` for critical services
- **Benefits**: Automatic recovery from failures, improved uptime

### 5. **Health Checks**

- **Enhanced**: More specific health check endpoints
- **Optimized**: Better timeout and retry configurations
- **Dependencies**: Service dependencies with health conditions
- **Benefits**: Faster failure detection, reliable service startup

### 6. **Security Enhancements**

- **Grafana**: Disabled user sign-ups, added security plugins
- **Environment**: Proper secret management with .env file
- **Networks**: Isolated network with custom subnet
- **Benefits**: Reduced attack surface, better access control

### 7. **Logging Configuration**

- **Driver**: JSON file logging for better log management
- **Rotation**: Configured log rotation (max 100MB, 3 files)
- **Benefits**: Better debugging, controlled disk usage

### 8. **Volume Management**

- **Named Volumes**: Proper volume naming and configuration
- **Data Persistence**: Separate volumes for different data types
- **Benefits**: Better data organization, easier backups

### 9. **Network Configuration**

- **Custom Network**: Isolated bridge network with subnet
- **Static IPs**: Configurable IP address management
- **Benefits**: Better security, predictable networking

### 10. **Development & Production Profiles**

- **Development**: Volume mounts for live reloading
- **Production**: Optimized resource allocation
- **GPU Support**: Optional GPU-only services
- **Benefits**: Flexible deployment options

## 📋 Service Architecture

### Core Services

1. **Ollama** (LLM inference) - GPU-accelerated language model serving
2. **ChromaDB** (Vector database) - Document embeddings and retrieval
3. **UI** (Streamlit) - Web interface for document interaction
4. **API** (FastAPI) - REST API for programmatic access

### Infrastructure Services

1. **Prometheus** - Metrics collection and monitoring
2. **Grafana** - Visualization and dashboards
3. **NVIDIA** - GPU validation and setup

## 🚀 Usage Examples

### Development Mode (Default)

```bash
docker-compose up
```

### Production Mode

```bash
docker-compose --profile prod up
```

### GPU-Only Services

```bash
docker-compose --profile gpu up nvidia
```

### Specific Services

```bash
docker-compose up ollama chroma ui
```

## 🔧 Environment Configuration

1. Copy `.env.example` to `.env`
2. Configure your environment variables
3. Adjust resource limits based on your hardware

### Key Environment Variables

- `MODEL`: Language model selection
- `EMBEDDINGS_MODEL_NAME`: Embedding model for documents
- `ANCLORA_API_TOKENS`: API authentication tokens
- `GRAFANA_USER/PASSWORD`: Grafana credentials

## 📊 Monitoring & Observability

- **Prometheus**: Available at `http://localhost:9090`
- **Grafana**: Available at `http://localhost:3000`
- **Health Checks**: All services include health monitoring
- **Metrics**: Built-in metrics collection for all services

## 🔒 Security Features

- Isolated Docker network
- JWT-based authentication
- Environment variable secrets
- Disabled Grafana user registration
- Resource limits and quotas

## 📈 Performance Optimizations

- Optimized health check intervals
- Proper resource reservations
- Efficient logging configuration
- Service dependency management
- Startup order optimization

## 🛠 Troubleshooting

### Common Issues

1. **GPU Not Available**: Run with `--profile gpu` or check NVIDIA drivers
2. **Port Conflicts**: Change ports in docker-compose.yml
3. **Memory Issues**: Adjust resource limits based on available RAM
4. **Service Dependencies**: Check service health with `docker-compose ps`

### Debug Commands

```bash
# Check service health
docker-compose ps

# View logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]

# Scale services
docker-compose up -d --scale ui=2
```

## 📝 Migration from Previous Version

1. **Backup**: Save your current docker-compose.yml
2. **Update**: Replace with the new configuration
3. **Environment**: Copy `.env.example` to `.env` and configure
4. **Volumes**: Existing volumes will be preserved
5. **Test**: Start with `docker-compose up` to verify functionality

## 🎯 Best Practices Implemented

- ✅ Semantic versioning and documentation
- ✅ Resource limits and health checks
- ✅ Security hardening
- ✅ Environment-based configuration
- ✅ Proper service dependencies
- ✅ Logging and monitoring
- ✅ Development/Production profiles
- ✅ Network isolation
- ✅ Volume management
- ✅ Error handling and recovery

This configuration provides a production-ready, scalable, and maintainable Docker Compose setup for the Anclora RAG system.
