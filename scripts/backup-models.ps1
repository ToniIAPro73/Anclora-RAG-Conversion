# =============================================================================
# Anclora RAG - Model Backup Script
# =============================================================================
# This script creates backups of Ollama models to prevent data loss
# =============================================================================

param(
    [string]$BackupPath = ".\backups\models",
    [switch]$Compress = $true,
    [int]$RetainDays = 30
)

# Configuration
$ContainerName = "anclora_rag-ollama-1"
$VolumeName = "anclora_rag_ollama_models"

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $(
        switch ($Level) {
            "ERROR" { "Red" }
            "WARNING" { "Yellow" }
            "SUCCESS" { "Green" }
            default { "White" }
        }
    )
}

# Create backup directory
function New-BackupDirectory {
    if (-not (Test-Path $BackupPath)) {
        New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
        Write-Log "Created backup directory: $BackupPath" "SUCCESS"
    }
}

# Backup models
function Backup-Models {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupName = "ollama-models-$timestamp"
    $tempPath = Join-Path $env:TEMP $backupName
    
    try {
        Write-Log "Starting model backup..."
        
        # Create temporary directory
        New-Item -ItemType Directory -Path $tempPath -Force | Out-Null
        
        # Copy models from container
        Write-Log "Copying models from container..."
        $copyResult = docker cp "${ContainerName}:/root/.ollama/models" $tempPath
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to copy models from container"
        }
        
        # Create final backup
        $finalBackupPath = Join-Path $BackupPath $backupName
        
        if ($Compress) {
            $archivePath = "$finalBackupPath.zip"
            Write-Log "Creating compressed backup: $archivePath"
            Compress-Archive -Path "$tempPath\*" -DestinationPath $archivePath -Force
            $backupSize = (Get-Item $archivePath).Length
        }
        else {
            Write-Log "Creating uncompressed backup: $finalBackupPath"
            Move-Item -Path $tempPath -Destination $finalBackupPath -Force
            $backupSize = (Get-ChildItem $finalBackupPath -Recurse | Measure-Object -Property Length -Sum).Sum
        }
        
        # Clean up temp directory
        if (Test-Path $tempPath) {
            Remove-Item -Path $tempPath -Recurse -Force
        }
        
        $backupSizeMB = [math]::Round($backupSize / 1MB, 2)
        Write-Log "Backup completed successfully. Size: ${backupSizeMB} MB" "SUCCESS"
        
        return $true
    }
    catch {
        Write-Log "Backup failed: $($_.Exception.Message)" "ERROR"
        
        # Clean up on failure
        if (Test-Path $tempPath) {
            Remove-Item -Path $tempPath -Recurse -Force
        }
        
        return $false
    }
}

# Clean old backups
function Remove-OldBackups {
    Write-Log "Cleaning up old backups (older than $RetainDays days)..."
    
    $cutoffDate = (Get-Date).AddDays(-$RetainDays)
    $oldBackups = Get-ChildItem -Path $BackupPath -Filter "ollama-models-*" | Where-Object { $_.CreationTime -lt $cutoffDate }
    
    foreach ($backup in $oldBackups) {
        try {
            Remove-Item -Path $backup.FullName -Recurse -Force
            Write-Log "Removed old backup: $($backup.Name)" "SUCCESS"
        }
        catch {
            Write-Log "Failed to remove old backup $($backup.Name): $($_.Exception.Message)" "WARNING"
        }
    }
}

# Verify Docker is running
function Test-DockerRunning {
    try {
        docker ps | Out-Null
        return $true
    }
    catch {
        Write-Log "Docker is not running or not accessible" "ERROR"
        return $false
    }
}

# Verify container exists
function Test-ContainerExists {
    $containers = docker ps -a --format "{{.Names}}"
    return $ContainerName -in $containers
}

# Main function
function Main {
    Write-Log "Starting Anclora RAG model backup process..."
    
    # Verify prerequisites
    if (-not (Test-DockerRunning)) {
        Write-Log "Docker is required but not running" "ERROR"
        exit 1
    }
    
    if (-not (Test-ContainerExists)) {
        Write-Log "Container $ContainerName not found" "ERROR"
        exit 1
    }
    
    # Create backup directory
    New-BackupDirectory
    
    # Perform backup
    if (Backup-Models) {
        # Clean old backups
        Remove-OldBackups
        Write-Log "Backup process completed successfully" "SUCCESS"
    }
    else {
        Write-Log "Backup process failed" "ERROR"
        exit 1
    }
}

# Run main function
Main