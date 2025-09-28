# =============================================================================
# Anclora RAG - Model Maintenance Scheduler (PowerShell)
# =============================================================================
# This script schedules regular model maintenance tasks including integrity
# checks, backups, and recovery operations with detailed logging.
# =============================================================================

param(
    [int]$IntervalMinutes = 60,
    [string]$LogDir = "logs",
    [string]$LogFile = "model_maintenance.log",
    [switch]$RunOnce = $false,
    [switch]$Verbose = $false
)

# Configuration
$RequiredModels = @("llama3")
$OllamaHost = "http://localhost:11434"
$MaxLogFiles = 10
$MaxLogSizeMB = 100

# Global variables
$Global:LogPath = Join-Path $LogDir $LogFile
$Global:MaintenanceCount = 0

# Logging functions
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [switch]$NoConsole
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"

    # Write to console if not suppressed
    if (!$NoConsole) {
        switch ($Level) {
            "ERROR" { Write-Host $logEntry -ForegroundColor Red }
            "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
            "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
            "INFO" { if ($Verbose) { Write-Host $logEntry -ForegroundColor Blue } }
            default { if ($Verbose) { Write-Host $logEntry -ForegroundColor White } }
        }
    }

    # Write to log file
    try {
        Add-Content -Path $Global:LogPath -Value $logEntry
    }
    catch {
        Write-Host "Failed to write to log file: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Initialize logging
function Initialize-Logging {
    # Create log directory if it doesn't exist
    if (!(Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force
        Write-Log "Created log directory: $LogDir"
    }

    # Rotate log files if necessary
    Rotate-LogFiles

    Write-Log "Model maintenance scheduler started" "SUCCESS"
    Write-Log "Interval: $IntervalMinutes minutes" "INFO"
    Write-Log "Required models: $($RequiredModels -join ', ')" "INFO"
}

# Rotate log files
function Rotate-LogFiles {
    try {
        if (Test-Path $Global:LogPath) {
            $logSize = (Get-Item $Global:LogPath).Length / 1MB
            if ($logSize -ge $MaxLogSizeMB) {
                # Rotate existing log files
                for ($i = $MaxLogFiles - 1; $i -ge 1; $i--) {
                    $oldFile = Join-Path $LogDir "${LogFile}.$i"
                    $newFile = Join-Path $LogDir "${LogFile}.$($i + 1)"
                    if (Test-Path $oldFile) {
                        Move-Item -Path $oldFile -Destination $newFile -Force
                    }
                }

                # Move current log to .1
                Move-Item -Path $Global:LogPath -Destination (Join-Path $LogDir "${LogFile}.1") -Force
                Write-Log "Log file rotated due to size limit ($($logSize.ToString('F2')) MB >= $MaxLogSizeMB MB)" "INFO" -NoConsole
            }
        }
    }
    catch {
        Write-Host "Failed to rotate log files: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test Ollama service availability
function Test-OllamaService {
    try {
        $response = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get -TimeoutSec 10
        Write-Log "Ollama service is available" "SUCCESS"
        return $true
    }
    catch {
        Write-Log "Ollama service is not available: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Get detailed model information
function Get-ModelDetails {
    param([string]$ModelName)

    try {
        $response = Invoke-RestMethod -Uri "$OllamaHost/api/show" -Method Post -Body (@{name = $ModelName} | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30

        $details = @{
            Name = $response.name
            Size = $response.size
            ParameterSize = $response.parameter_size
            QuantizationLevel = $response.quantization_level
            Template = $response.template
            System = $response.system
            Details = $response.details
        }

        Write-Log "Retrieved details for model $ModelName" "INFO"
        return $details
    }
    catch {
        Write-Log "Failed to get details for model $ModelName : $($_.Exception.Message)" "WARNING"
        return $null
    }
}

# Comprehensive model health check
function Test-ModelHealth {
    param([string]$ModelName)

    Write-Log "Starting comprehensive health check for model: $ModelName" "INFO"

    $health = @{
        ModelName = $ModelName
        Timestamp = Get-Date
        Checks = @{}
        OverallStatus = "UNKNOWN"
    }

    # 1. Check if model exists in Ollama
    try {
        $response = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get -TimeoutSec 10
        $modelExists = $response.models | Where-Object { $_.name -eq $ModelName } | Measure-Object | Select-Object -ExpandProperty Count

        $health.Checks["ModelExists"] = $modelExists -gt 0
        Write-Log "Model exists check: $($modelExists -gt 0)" "INFO"
    }
    catch {
        $health.Checks["ModelExists"] = $false
        Write-Log "Model exists check failed: $($_.Exception.Message)" "ERROR"
    }

    # 2. Get model details
    if ($health.Checks["ModelExists"]) {
        $details = Get-ModelDetails -ModelName $ModelName
        if ($details) {
            $health.Details = $details
            $health.Checks["DetailsRetrieved"] = $true

            # 3. Test model loading
            try {
                $testResponse = Invoke-RestMethod -Uri "$OllamaHost/api/generate" -Method Post -Body (@{
                    model = $ModelName
                    prompt = "test"
                    stream = $false
                } | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 60

                $health.Checks["ModelLoads"] = $true
                Write-Log "Model loading test passed" "SUCCESS"
            }
            catch {
                $health.Checks["ModelLoads"] = $false
                Write-Log "Model loading test failed: $($_.Exception.Message)" "ERROR"
            }
        }
        else {
            $health.Checks["DetailsRetrieved"] = $false
        }
    }

    # 4. Run backup integrity check
    try {
        $backupScript = Join-Path $PSScriptRoot "backup-models.ps1"
        if (Test-Path $backupScript) {
            $integrityResult = & $backupScript -VerifyOnly:$true
            $health.Checks["IntegrityVerified"] = $LASTEXITCODE -eq 0
            Write-Log "Integrity verification: $($LASTEXITCODE -eq 0)" "INFO"
        }
        else {
            $health.Checks["IntegrityVerified"] = $false
            Write-Log "Backup script not found: $backupScript" "WARNING"
        }
    }
    catch {
        $health.Checks["IntegrityVerified"] = $false
        Write-Log "Integrity verification failed: $($_.Exception.Message)" "ERROR"
    }

    # Determine overall status
    $allChecksPassed = $true
    foreach ($check in $health.Checks.Values) {
        if ($check -eq $false) {
            $allChecksPassed = $false
            break
        }
    }

    $health.OverallStatus = if ($allChecksPassed) { "HEALTHY" } else { "UNHEALTHY" }
    Write-Log "Overall health status for $ModelName : $($health.OverallStatus)" "INFO"

    return $health
}

# Perform maintenance actions
function Invoke-ModelMaintenance {
    param([string]$ModelName)

    Write-Log "Performing maintenance for model: $ModelName" "INFO"

    $actions = @()

    # 1. Run backup script
    try {
        $backupScript = Join-Path $PSScriptRoot "backup-models.ps1"
        if (Test-Path $backupScript) {
            & $backupScript
            if ($LASTEXITCODE -eq 0) {
                $actions += "Backup completed"
                Write-Log "Backup completed successfully" "SUCCESS"
            }
            else {
                $actions += "Backup failed"
                Write-Log "Backup failed" "ERROR"
            }
        }
    }
    catch {
        $actions += "Backup error: $($_.Exception.Message)"
        Write-Log "Backup error: $($_.Exception.Message)" "ERROR"
    }

    # 2. Clean old backups
    try {
        $oldBackups = Get-ChildItem -Path "model_backups" -Name "${ModelName}_*.backup" | Sort-Object -Descending | Select-Object -Skip 5
        foreach ($backup in $oldBackups) {
            Remove-Item -Path (Join-Path "model_backups" $backup) -Force -ErrorAction SilentlyContinue
        }
        $actions += "Old backups cleaned"
        Write-Log "Old backups cleaned" "INFO"
    }
    catch {
        $actions += "Backup cleanup error: $($_.Exception.Message)"
        Write-Log "Backup cleanup error: $($_.Exception.Message)" "WARNING"
    }

    return $actions
}

# Main maintenance cycle
function Start-MaintenanceCycle {
    $Global:MaintenanceCount++

    Write-Log "=== Starting maintenance cycle #$Global:MaintenanceCount ===" "INFO"

    # Check Ollama service
    if (!(Test-OllamaService)) {
        Write-Log "Skipping maintenance cycle due to Ollama service unavailability" "WARNING"
        return
    }

    $cycleResults = @{}

    # Process each model
    foreach ($model in $RequiredModels) {
        Write-Log "Processing model: $model" "INFO"

        # Health check
        $health = Test-ModelHealth -ModelName $model
        $cycleResults[$model] = $health

        # Maintenance actions if needed
        if ($health.OverallStatus -eq "UNHEALTHY") {
            Write-Log "Model $model is unhealthy, performing maintenance" "WARNING"
            $maintenanceActions = Invoke-ModelMaintenance -ModelName $model
            $cycleResults[$model].MaintenanceActions = $maintenanceActions
        }
        else {
            Write-Log "Model $model is healthy, skipping maintenance" "INFO"
        }
    }

    # Summary
    $healthyModels = ($cycleResults.Values | Where-Object { $_.OverallStatus -eq "HEALTHY" }).Count
    $totalModels = $cycleResults.Count

    Write-Log "Maintenance cycle #$Global:MaintenanceCount completed - $healthyModels/$totalModels models healthy" "SUCCESS"

    return $cycleResults
}

# Main function
function Main {
    Write-Host "Anclora RAG Model Maintenance Scheduler" -ForegroundColor Cyan
    Write-Host "=====================================" -ForegroundColor Cyan

    # Initialize logging
    Initialize-Logging

    try {
        if ($RunOnce) {
            # Run once and exit
            Start-MaintenanceCycle | Out-Null
        }
        else {
            # Continuous monitoring
            Write-Log "Starting continuous maintenance schedule (interval: $IntervalMinutes minutes)" "INFO"

            while ($true) {
                $startTime = Get-Date
                Start-MaintenanceCycle | Out-Null
                $endTime = Get-Date

                $duration = $endTime - $startTime
                Write-Log "Maintenance cycle completed in $($duration.TotalSeconds.ToString('F1')) seconds" "INFO"

                # Wait for next cycle
                $waitTime = ($IntervalMinutes * 60) - $duration.TotalSeconds
                if ($waitTime -gt 0) {
                    Start-Sleep -Seconds $waitTime
                }
            }
        }
    }
    catch {
        Write-Log "Fatal error in maintenance scheduler: $($_.Exception.Message)" "ERROR"
        Write-Host "Fatal error: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    finally {
        Write-Log "Model maintenance scheduler stopped" "INFO"
    }
}

# Handle Ctrl+C gracefully
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Write-Log "Model maintenance scheduler stopped by user" "WARNING"
}

# Run main function
Main