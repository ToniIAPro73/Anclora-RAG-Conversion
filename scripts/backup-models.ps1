# =============================================================================
# Anclora RAG - Model Backup and Integrity System (PowerShell)
# =============================================================================
# This script creates backups of Ollama models with checksums for integrity
# verification and automatic recovery.
# =============================================================================

param(
    [string]$OllamaHost = "http://localhost:11434",
    [string]$BackupDir = "model_backups",
    [int]$MaxRetries = 3,
    [int]$RetryDelay = 5,
    [switch]$UseDocker = $false,
    [switch]$Force = $false
)

# Configuration
$RequiredModels = @("llama3")
# Auto-detect Ollama host based on environment
if ($env:DOCKER_CONTAINER) {
    $OllamaHost = "http://ollama:11434"  # Inside Docker network
} else {
    $OllamaHost = "http://localhost:11434"  # External access
}
$ChecksumFile = Join-Path $BackupDir "model_checksums.sha256"

# Logging functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Create backup directory
function Initialize-BackupDir {
    if (!(Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force
        Write-Info "Created backup directory: $BackupDir"
    }
}

# Get model file path
function Get-ModelPath {
    param([string]$ModelName)

    try {
        if ($UseDocker) {
            $result = docker exec anclora_rag-ollama-1 ollama show $ModelName 2>$null
            if ($LASTEXITCODE -eq 0) {
                # Extract model path from ollama show output
                $lines = $result -split "`n"
                foreach ($line in $lines) {
                    if ($line -match "Parameters:\s*(.+)") {
                        return $matches[1]
                    }
                }
            }
        }
        else {
            # For local Ollama, models are typically in ~/.ollama/models
            $ollamaDir = Join-Path $env:USERPROFILE ".ollama"
            $modelPath = Join-Path $ollamaDir "models"
            return $modelPath
        }
    }
    catch {
        Write-Warning "Could not determine model path for $ModelName"
        return $null
    }
}

# Calculate file checksum
function Get-FileChecksum {
    param([string]$FilePath)

    try {
        $hash = Get-FileHash -Path $FilePath -Algorithm SHA256
        return $hash.Hash
    }
    catch {
        Write-Error "Failed to calculate checksum for $FilePath : $($_.Exception.Message)"
        return $null
    }
}

# Save checksums to file
function Save-Checksums {
    param([hashtable]$Checksums)

    $content = ""
    foreach ($model in $Checksums.Keys) {
        $content += "$($Checksums[$model])  $model`n"
    }

    $content | Out-File -FilePath $ChecksumFile -Encoding UTF8
    Write-Info "Checksums saved to: $ChecksumFile"
}

# Load existing checksums
function Load-Checksums {
    $checksums = @{}

    if (Test-Path $ChecksumFile) {
        $lines = Get-Content $ChecksumFile
        foreach ($line in $lines) {
            if ($line -match "^(\w+)\s+(.+)$") {
                $checksums[$matches[2]] = $matches[1]
            }
        }
    }

    return $checksums
}

# Verify model integrity
function Test-ModelIntegrity {
    param([string]$ModelName)

    Write-Info "Verifying integrity of model: $ModelName"

    $modelPath = Get-ModelPath -ModelName $ModelName
    if (!$modelPath) {
        return $false
    }

    $currentChecksum = Get-FileChecksum -FilePath $modelPath
    if (!$currentChecksum) {
        return $false
    }

    $existingChecksums = Load-Checksums
    $expectedChecksum = $existingChecksums[$ModelName]

    if ($expectedChecksum -and $currentChecksum -eq $expectedChecksum) {
        Write-Success "Model $ModelName integrity verified"
        return $true
    }
    else {
        Write-Warning "Model $ModelName integrity check failed"
        return $false
    }
}

# Create model backup
function Backup-Model {
    param([string]$ModelName)

    Write-Info "Creating backup for model: $ModelName"

    $modelPath = Get-ModelPath -ModelName $ModelName
    if (!$modelPath) {
        Write-Error "Cannot backup model $ModelName - path not found"
        return $false
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = Join-Path $BackupDir "${ModelName}_${timestamp}.backup"
    $checksumFile = Join-Path $BackupDir "${ModelName}_${timestamp}.sha256"

    try {
        # Create backup
        Copy-Item -Path $modelPath -Destination $backupFile -Force
        Write-Success "Model backup created: $backupFile"

        # Calculate and save checksum
        $checksum = Get-FileChecksum -FilePath $backupFile
        if ($checksum) {
            $checksum | Out-File -FilePath $checksumFile -Encoding UTF8
            Write-Success "Checksum saved: $checksumFile"
        }

        # Update master checksums file
        $checksums = Load-Checksums
        $checksums[$ModelName] = $checksum
        Save-Checksums -Checksums $checksums

        return $true
    }
    catch {
        Write-Error "Failed to backup model $ModelName : $($_.Exception.Message)"
        return $false
    }
}

# Restore model from backup
function Restore-Model {
    param([string]$ModelName)

    Write-Info "Restoring model from backup: $ModelName"

    # Find latest backup
    $backupFiles = Get-ChildItem -Path $BackupDir -Name "${ModelName}_*.backup" | Sort-Object -Descending
    if ($backupFiles.Count -eq 0) {
        Write-Error "No backup found for model $ModelName"
        return $false
    }

    $latestBackup = $backupFiles[0]
    $backupPath = Join-Path $BackupDir $latestBackup

    $modelPath = Get-ModelPath -ModelName $ModelName
    if (!$modelPath) {
        Write-Error "Cannot restore model $ModelName - destination path not found"
        return $false
    }

    try {
        # Restore backup
        Copy-Item -Path $backupPath -Destination $modelPath -Force
        Write-Success "Model $ModelName restored from: $backupPath"

        # Verify integrity after restore
        if (Test-ModelIntegrity -ModelName $ModelName) {
            Write-Success "Model integrity verified after restore"
            return $true
        }
        else {
            Write-Warning "Model integrity check failed after restore"
            return $false
        }
    }
    catch {
        Write-Error "Failed to restore model $ModelName : $($_.Exception.Message)"
        return $false
    }
}

# Clean old backups
function Clear-OldBackups {
    param([int]$KeepLast = 5)

    Write-Info "Cleaning old backups (keeping last $KeepLast)"

    foreach ($model in $RequiredModels) {
        $backupFiles = Get-ChildItem -Path $BackupDir -Name "${ModelName}_*.backup" | Sort-Object -Descending

        if ($backupFiles.Count -gt $KeepLast) {
            $filesToDelete = $backupFiles[$KeepLast..($backupFiles.Count - 1)]

            foreach ($file in $filesToDelete) {
                $filePath = Join-Path $BackupDir $file
                Remove-Item -Path $filePath -Force -ErrorAction SilentlyContinue
                Write-Info "Removed old backup: $file"
            }
        }
    }
}

# Main function
function Main {
    Write-Info "Starting Anclora RAG model backup and integrity system..."

    # Initialize backup directory
    Initialize-BackupDir

    # Process each required model
    foreach ($model in $RequiredModels) {
        Write-Info "Processing model: $model"

        # Check if model exists
        $modelExists = $false
        try {
            if ($UseDocker) {
                $result = docker exec anclora_rag-ollama-1 ollama list 2>$null
                $modelExists = $result -match $model
            }
            else {
                $response = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get -TimeoutSec 10
                $modelExists = $response.models | Where-Object { $_.name -eq $model } | Measure-Object | Select-Object -ExpandProperty Count
            }
        }
        catch {
            $modelExists = $false
        }

        if ($modelExists) {
            # Verify model integrity
            if (Test-ModelIntegrity -ModelName $model) {
                Write-Success "Model $model is healthy"

                # Create backup if forced or if no backup exists
                $hasBackup = (Load-Checksums).ContainsKey($model)
                if ($Force -or !$hasBackup) {
                    if (Backup-Model -ModelName $model) {
                        Write-Success "Backup completed for model $model"
                    }
                }
            }
            else {
                Write-Warning "Model $model integrity check failed"

                # Try to restore from backup
                if (Restore-Model -ModelName $model) {
                    Write-Success "Model $model restored from backup"
                }
                else {
                    Write-Error "Failed to restore model $model from backup"
                    # Try to re-download the model
                    Write-Info "Attempting to re-download model $model"
                    try {
                        if ($UseDocker) {
                            docker exec anclora_rag-ollama-1 ollama pull $model
                        }
                        else {
                            $body = @{ name = $model } | ConvertTo-Json
                            Invoke-RestMethod -Uri "$OllamaHost/api/pull" -Method Post -Body $body -ContentType "application/json"
                        }
                        Write-Success "Model $model re-downloaded successfully"
                    }
                    catch {
                        Write-Error "Failed to re-download model $model"
                    }
                }
            }
        }
        else {
            Write-Warning "Model $model not found, skipping backup"
        }
    }

    # Clean old backups
    Clear-OldBackups -KeepLast 5

    Write-Success "Model backup and integrity system completed!"
}

# Run main function
Main