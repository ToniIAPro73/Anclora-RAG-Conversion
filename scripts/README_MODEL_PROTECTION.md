# Anclora RAG - Model Protection System

## Overview

This document describes the comprehensive solution implemented to prevent Llama3 model loss and ensure continuous availability in the Anclora RAG system.

## Problem Statement

The Llama3 model was being lost intermittently, causing service disruptions and requiring manual intervention to restore functionality. This affected the reliability and user experience of the RAG system.

## Solution Architecture

The implemented solution consists of multiple layers of protection:

### 1. Model Backup System (`backup-models.ps1` / `backup-models.sh`)

**Features:**
- Automatic model backup with checksum verification
- Integrity validation using SHA256 hashes
- Automatic recovery from backup when corruption is detected
- Backup rotation (keeps last 5 backups by default)
- Cross-platform support (Windows PowerShell + Linux Bash)

**Usage:**
```bash
# PowerShell (Windows)
.\scripts\backup-models.ps1

# Bash (Linux/Docker)
./scripts/backup-models.sh

# Verify only mode
./scripts/backup-models.sh --verify-only
```

### 2. Enhanced Health Checks

**Docker Compose Integration:**
- Modified `ollama` service healthcheck to include integrity verification
- Automatic model re-download if missing
- Integration with backup system for corruption detection

**Health Check Process:**
1. Verify model exists in Ollama
2. Check model integrity against stored checksums
3. Attempt recovery from backup if corruption detected
4. Re-download model if backup recovery fails

### 3. Maintenance Scheduler (`model-maintenance-scheduler.ps1` / `model-maintenance-scheduler.sh`)

**Features:**
- Automated maintenance cycles with configurable intervals
- Comprehensive health monitoring
- Detailed logging with rotation
- Automatic backup and cleanup operations
- Integration with monitoring systems

**Configuration Options:**
- `--interval MINUTES`: Set maintenance interval (default: 60)
- `--run-once`: Execute once instead of continuous monitoring
- `--verbose`: Enable detailed logging output

**Usage:**
```bash
# Start continuous maintenance (Windows)
.\scripts\model-maintenance-scheduler.ps1

# Start continuous maintenance (Linux)
./scripts/model-maintenance-scheduler.sh

# Run once with verbose output
.\scripts\model-maintenance-scheduler.ps1 -RunOnce -Verbose
```

### 4. Enhanced Monitoring System (`monitor-models.ps1`)

**Features:**
- Real-time model availability monitoring
- Detailed health metrics collection
- Integration with maintenance scheduler
- Alert system for model failures
- Historical metrics storage in JSON format

**Metrics Collected:**
- Model availability status
- Integrity verification results
- Response times and error rates
- Maintenance action history
- Health trend analysis

**Usage:**
```powershell
# Start enhanced monitoring
.\scripts\monitor-models.ps1

# Start with custom interval and maintenance
.\scripts\monitor-models.ps1 -CheckInterval 180 -EnableMaintenance -MaintenanceInterval 6
```

## Implementation Details

### Checksum Verification Process

1. **Initial Backup Creation:**
   - Models are automatically backed up with SHA256 checksums
   - Checksums stored in `model_backups/model_checksums.sha256`
   - Backup metadata includes timestamps and file sizes

2. **Integrity Verification:**
   - Compare current model checksums against stored values
   - Automatic detection of corruption or tampering
   - Immediate alerts on integrity failures

3. **Recovery Process:**
   - Automatic restoration from most recent valid backup
   - Fallback to model re-download if backup unavailable
   - Verification of restored model integrity

### Monitoring Integration

The solution integrates with existing monitoring infrastructure:

- **Docker Health Checks:** Enhanced to include integrity verification
- **Log Aggregation:** Structured logging with rotation
- **Metrics Collection:** JSON-based metrics for external monitoring systems
- **Alert System:** Configurable notifications on model failures

### Backup Strategy

- **Automatic Backups:** Created during maintenance cycles
- **Retention Policy:** Keeps 5 most recent backups per model
- **Storage Location:** `model_backups/` directory
- **Compression:** Uses tar compression for efficient storage
- **Checksums:** SHA256 verification for all backups

## Deployment Instructions

### 1. Initial Setup

1. **Copy Scripts:** Ensure all scripts are in the `scripts/` directory
2. **Set Permissions:** Make shell scripts executable
   ```bash
   chmod +x scripts/backup-models.sh scripts/model-maintenance-scheduler.sh
   ```

3. **Create Backup Directory:**
   ```bash
   mkdir -p model_backups logs
   ```

### 2. Docker Integration

The solution is automatically integrated with Docker Compose:

- Health checks run every 60 seconds
- Automatic model verification on container startup
- Graceful handling of model corruption scenarios

### 3. Start Services

```bash
# Start with Docker Compose (includes enhanced health checks)
docker compose up -d

# Start maintenance scheduler
./scripts/model-maintenance-scheduler.sh &

# Start enhanced monitoring
.\scripts\monitor-models.ps1
```

## Configuration Options

### Environment Variables

```bash
# Model configuration
MODEL=llama3
OLLAMA_HOST=http://localhost:11434

# Maintenance configuration
MAINTENANCE_INTERVAL=60
BACKUP_RETENTION_COUNT=5
LOG_LEVEL=INFO
```

### Script Parameters

All scripts support standard help options:

```bash
.\scripts\backup-models.ps1 -?
./scripts/model-maintenance-scheduler.sh --help
```

## Monitoring and Alerting

### Log Files

- `logs/model_maintenance.log`: Maintenance scheduler logs
- `model-monitor.log`: Monitoring system logs
- `model_backups/model_checksums.sha256`: Integrity checksums

### Metrics

- `model-metrics.json`: Detailed health metrics and history
- Includes timestamps, status changes, and performance data

### Alert Conditions

The system generates alerts for:
- Model missing from Ollama
- Integrity checksum failures
- Backup restoration failures
- Service unavailability
- Maintenance action failures

## Troubleshooting

### Common Issues

1. **Model Not Found:**
   - Check Docker container logs
   - Verify Ollama service connectivity
   - Review maintenance scheduler logs

2. **Integrity Check Failures:**
   - Check backup directory permissions
   - Verify checksum file integrity
   - Review model file permissions

3. **Backup Failures:**
   - Ensure sufficient disk space
   - Check write permissions on backup directory
   - Verify model file accessibility

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Windows
.\scripts\model-maintenance-scheduler.ps1 -Verbose

# Linux
./scripts/model-maintenance-scheduler.sh --verbose
```

## Performance Impact

The solution is designed for minimal performance impact:

- **Health Checks:** ~5-10 seconds per cycle
- **Integrity Verification:** ~2-5 seconds per model
- **Backup Creation:** ~30-60 seconds per model
- **Memory Usage:** <50MB additional
- **Storage:** ~5x model size for backups

## Maintenance Tasks

### Regular Maintenance

1. **Weekly:** Review log files and metrics
2. **Monthly:** Clean old backup files if needed
3. **Quarterly:** Update scripts and dependencies

### Log Rotation

- Automatic log rotation when files exceed 100MB
- Maximum 10 rotated files kept
- Configurable size and count limits

## Security Considerations

- Checksums prevent tampering with model files
- Backup encryption can be added if required
- Access controls on backup directories
- Audit logging for all maintenance actions

## Future Enhancements

Potential improvements for the next version:

1. **Web Dashboard:** Visual monitoring interface
2. **Remote Backups:** Cloud storage integration
3. **Predictive Maintenance:** ML-based failure prediction
4. **Multi-Model Support:** Enhanced support for additional models
5. **API Integration:** REST endpoints for external monitoring

## Support

For issues or questions regarding the Model Protection System:

1. Check the troubleshooting section above
2. Review the log files for error details
3. Verify all scripts have proper permissions
4. Ensure Docker services are running correctly

---

*This solution ensures continuous availability of Llama3 models in the Anclora RAG system through comprehensive backup, integrity verification, and automated recovery mechanisms.*