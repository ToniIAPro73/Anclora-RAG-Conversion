# =============================================================================
# Anclora RAG - Manual Model Backup Creator
# =============================================================================
# This script creates a manual backup of the Llama3 model by copying it
# from the Docker container to the host filesystem.
# =============================================================================

param(
    [switch]$Force = $false
)

# Configuration
$ContainerName = "anclora_rag-ollama-1"
$ModelName = "llama3"
$BackupDir = "model_backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "Anclora RAG - Manual Model Backup Creator" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if container is running
try {
    $container = docker ps -q -f name=$ContainerName
    if (!$container) {
        Write-Host "Error: Container $ContainerName is not running" -ForegroundColor Red
        Write-Host "Please start the container first: docker compose up -d" -ForegroundColor Yellow
        exit 1
    }
}
catch {
    Write-Host "Error: Cannot access Docker. Please ensure Docker is running." -ForegroundColor Red
    exit 1
}

Write-Host "✓ Container $ContainerName is running" -ForegroundColor Green

# Create backup directory
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "✓ Created backup directory: $BackupDir" -ForegroundColor Green
}

# Check if model exists in container
Write-Host "Checking model in container..." -ForegroundColor Blue
try {
    $modelList = docker exec $ContainerName ollama list
    if ($modelList -match $ModelName) {
        Write-Host "✓ Model $ModelName found in container" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Model $ModelName not found in container" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "✗ Error checking model: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Find model files in container
Write-Host "Finding model files..." -ForegroundColor Blue
try {
    $modelFiles = docker exec $ContainerName find /root/.ollama/models -name "*$ModelName*" -type f 2>$null
    if ($modelFiles) {
        Write-Host "✓ Found model files:" -ForegroundColor Green
        $modelFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
    }
    else {
        Write-Host "✗ No model files found" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "✗ Error finding model files: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Create backup
$BackupFile = Join-Path $BackupDir "${ModelName}_${Timestamp}.backup"
$ChecksumFile = Join-Path $BackupDir "${ModelName}_${Timestamp}.sha256"

Write-Host "Creating backup..." -ForegroundColor Blue
Write-Host "Backup file: $BackupFile" -ForegroundColor Gray

try {
    # Create tar backup of model files
    $tarCommand = "cd /root/.ollama/models && tar -czf /tmp/model_backup.tar.gz $(echo '$modelFiles' | tr '\n' ' ')"
    docker exec $ContainerName bash -c $tarCommand

    # Copy backup to host
    docker cp "${ContainerName}:/tmp/model_backup.tar.gz" $BackupFile

    # Clean up temporary file
    docker exec $ContainerName rm /tmp/model_backup.tar.gz

    Write-Host "✓ Backup created successfully: $BackupFile" -ForegroundColor Green

    # Calculate checksum
    $checksum = Get-FileHash -Path $BackupFile -Algorithm SHA256
    $checksum.Hash | Out-File -FilePath $ChecksumFile -Encoding UTF8

    Write-Host "✓ Checksum saved: $ChecksumFile" -ForegroundColor Green
    Write-Host "  Checksum: $($checksum.Hash)" -ForegroundColor Gray

    # Update master checksums file
    $MasterChecksumFile = Join-Path $BackupDir "model_checksums.sha256"
    if (Test-Path $MasterChecksumFile) {
        Add-Content -Path $MasterChecksumFile -Value "$($checksum.Hash)  $ModelName"
    }
    else {
        "$($checksum.Hash)  $ModelName" | Out-File -FilePath $MasterChecksumFile -Encoding UTF8
    }

    Write-Host "✓ Master checksums updated" -ForegroundColor Green

}
catch {
    Write-Host "✗ Error creating backup: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Show backup summary
Write-Host "`nBackup Summary:" -ForegroundColor Yellow
Write-Host "===============" -ForegroundColor Yellow
Write-Host "Model: $ModelName" -ForegroundColor White
Write-Host "Backup file: $(Split-Path $BackupFile -Leaf)" -ForegroundColor White
Write-Host "Size: $([math]::Round((Get-Item $BackupFile).Length / 1GB, 2)) GB" -ForegroundColor White
Write-Host "Checksum: $($checksum.Hash)" -ForegroundColor White
Write-Host "Timestamp: $(Get-Date)" -ForegroundColor White

Write-Host "`n✓ Manual backup completed successfully!" -ForegroundColor Green