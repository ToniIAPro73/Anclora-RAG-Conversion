# =============================================================================
# Anclora RAG - Enhanced Continuous Model Monitor
# =============================================================================
# This script continuously monitors model availability, integrity, and health
# with enhanced metrics and automatic recovery capabilities.
# =============================================================================

param(
    [int]$CheckInterval = 300, # 5 minutes
    [string]$LogFile = "model-monitor.log",
    [switch]$SendAlerts = $false,
    [switch]$EnableMaintenance = $true,
    [int]$MaintenanceInterval = 4, # Run maintenance every 4 cycles
    [switch]$Verbose = $false
)

# Configuration
$RequiredModels = @("llama3")
$OllamaHost = "http://localhost:11434"
$MetricsFile = "model-metrics.json"
$MaintenanceScript = Join-Path $PSScriptRoot "model-maintenance-scheduler.ps1"

# Enhanced logging function with metrics
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
    Add-Content -Path $LogFile -Value $logEntry
}

# Load metrics from file
function Get-Metrics {
    if (Test-Path $MetricsFile) {
        try {
            $metrics = Get-Content $MetricsFile | ConvertFrom-Json
            return $metrics
        }
        catch {
            return $null
        }
    }
    return $null
}

# Save metrics to file
function Save-Metrics {
    param([PSObject]$Metrics)

    try {
        $Metrics | ConvertTo-Json -Depth 3 | Out-File -FilePath $MetricsFile -Encoding UTF8
    }
    catch {
        Write-Log "Failed to save metrics: $($_.Exception.Message)" "ERROR"
    }
}

# Update model metrics
function Update-ModelMetrics {
    param(
        [string]$ModelName,
        [string]$Status,
        [hashtable]$HealthDetails = @{}
    )

    $metrics = Get-Metrics
    if (!$metrics) {
        $metrics = @{
            Models = @{}
            LastUpdated = Get-Date
            TotalChecks = 0
            TotalFailures = 0
        }
    }

    if (!$metrics.Models.ContainsKey($ModelName)) {
        $metrics.Models[$ModelName] = @{
            Status = "UNKNOWN"
            LastCheck = Get-Date
            CheckCount = 0
            FailureCount = 0
            HealthHistory = @()
            LastHealthDetails = @{}
        }
    }

    $modelMetrics = $metrics.Models[$ModelName]
    $modelMetrics.Status = $Status
    $modelMetrics.LastCheck = Get-Date
    $modelMetrics.CheckCount++
    $modelMetrics.LastHealthDetails = $HealthDetails

    if ($Status -eq "UNHEALTHY") {
        $modelMetrics.FailureCount++
        $metrics.TotalFailures++
    }

    # Keep only last 100 health records
    $modelMetrics.HealthHistory += @{
        Timestamp = Get-Date
        Status = $Status
        Details = $HealthDetails
    }

    if ($modelMetrics.HealthHistory.Count -gt 100) {
        $modelMetrics.HealthHistory = $modelMetrics.HealthHistory[-100..-1]
    }

    $metrics.TotalChecks++
    $metrics.LastUpdated = Get-Date

    Save-Metrics -Metrics $metrics
    Write-Log "Updated metrics for model $ModelName - Status: $Status" "INFO"
}

# Check model availability
function Test-ModelAvailability {
    try {
        $response = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get -TimeoutSec 10
        $availableModels = $response.models | Select-Object -ExpandProperty name
        
        $missingModels = @()
        foreach ($model in $RequiredModels) {
            if ($model -notin $availableModels) {
                $missingModels += $model
            }
        }
        
        return @{
            Success = $true
            AvailableModels = $availableModels
            MissingModels = $missingModels
        }
    }
    catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

# Send alert (placeholder - implement your preferred notification method)
function Send-Alert {
    param([string]$Message)
    
    if ($SendAlerts) {
        Write-Log "ALERT: $Message" "ERROR"
        # TODO: Implement email, Slack, or other notification system
        # Example: Send-MailMessage or Invoke-RestMethod to webhook
    }
}

# Enhanced model availability check with detailed health metrics
function Test-ModelAvailability {
    try {
        $response = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get -TimeoutSec 10
        $availableModels = $response.models | Select-Object -ExpandProperty name

        $missingModels = @()
        $modelHealth = @{}

        foreach ($model in $RequiredModels) {
            if ($model -notin $availableModels) {
                $missingModels += $model
                $modelHealth[$model] = "MISSING"
            }
            else {
                # Perform detailed health check
                $healthDetails = Test-ModelHealth -ModelName $model
                $modelHealth[$model] = $healthDetails.OverallStatus
            }
        }

        return @{
            Success = $true
            AvailableModels = $availableModels
            MissingModels = $missingModels
            ModelHealth = $modelHealth
        }
    }
    catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

# Detailed model health check
function Test-ModelHealth {
    param([string]$ModelName)

    $health = @{
        ModelName = $ModelName
        Timestamp = Get-Date
        Checks = @{}
        OverallStatus = "UNKNOWN"
    }

    # 1. Model exists check
    try {
        $response = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get -TimeoutSec 10
        $modelExists = $response.models | Where-Object { $_.name -eq $ModelName } | Measure-Object | Select-Object -ExpandProperty Count
        $health.Checks["ModelExists"] = $modelExists -gt 0
    }
    catch {
        $health.Checks["ModelExists"] = $false
    }

    # 2. Model details check
    if ($health.Checks["ModelExists"]) {
        try {
            $detailsResponse = Invoke-RestMethod -Uri "$OllamaHost/api/show" -Method Post -Body (@{name = $ModelName} | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30
            $health.Checks["DetailsRetrieved"] = $true
            $health.Details = $detailsResponse
        }
        catch {
            $health.Checks["DetailsRetrieved"] = $false
        }
    }

    # 3. Model functionality check
    if ($health.Checks["ModelExists"]) {
        try {
            $testResponse = Invoke-RestMethod -Uri "$OllamaHost/api/generate" -Method Post -Body (@{
                model = $ModelName
                prompt = "health check"
                stream = $false
            } | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 60
            $health.Checks["ModelFunctional"] = $true
        }
        catch {
            $health.Checks["ModelFunctional"] = $false
        }
    }

    # 4. Integrity check using backup system
    try {
        $backupScript = Join-Path $PSScriptRoot "backup-models.ps1"
        if (Test-Path $backupScript) {
            $integrityResult = & $backupScript -VerifyOnly:$true 2>$null
            $health.Checks["IntegrityVerified"] = $LASTEXITCODE -eq 0
        }
        else {
            $health.Checks["IntegrityVerified"] = $false
        }
    }
    catch {
        $health.Checks["IntegrityVerified"] = $false
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
    return $health
}

# Enhanced monitoring loop with metrics and maintenance integration
function Start-Monitoring {
    Write-Log "Starting enhanced Anclora RAG model monitoring..." "SUCCESS"
    Write-Log "Check interval: $CheckInterval seconds" "INFO"
    Write-Log "Required models: $($RequiredModels -join ', ')" "INFO"
    Write-Log "Maintenance integration: $EnableMaintenance" "INFO"

    $cycleCount = 0

    while ($true) {
        $cycleCount++
        $startTime = Get-Date

        Write-Log "=== Starting monitoring cycle #$cycleCount ===" "INFO"

        $result = Test-ModelAvailability

        if ($result.Success) {
            # Update metrics for each model
            foreach ($model in $RequiredModels) {
                $status = $result.ModelHealth[$model]
                $healthDetails = if ($status -ne "MISSING") { Test-ModelHealth -ModelName $model } else { @{} }
                Update-ModelMetrics -ModelName $model -Status $status -HealthDetails $healthDetails
            }

            if ($result.MissingModels.Count -eq 0) {
                $healthyModels = ($result.ModelHealth.Values | Where-Object { $_ -eq "HEALTHY" }).Count
                $totalModels = $result.ModelHealth.Count
                Write-Log "All models available - $healthyModels/$totalModels healthy" "SUCCESS"

                # Show detailed health status
                foreach ($model in $RequiredModels) {
                    $status = $result.ModelHealth[$model]
                    Write-Log "  $model : $status" "INFO"
                }
            }
            else {
                $message = "Missing models detected: $($result.MissingModels -join ', ')"
                Write-Log $message "WARNING"
                Send-Alert $message

                # Attempt to trigger model download
                Write-Log "Attempting to trigger model download via ensure-models script..." "INFO"
                try {
                    & "$PSScriptRoot\ensure-models.ps1"
                }
                catch {
                    Write-Log "Failed to run ensure-models script: $($_.Exception.Message)" "ERROR"
                }
            }

            # Run maintenance on schedule
            if ($EnableMaintenance -and ($cycleCount % $MaintenanceInterval -eq 0)) {
                Write-Log "Running scheduled maintenance..." "INFO"
                try {
                    if (Test-Path $MaintenanceScript) {
                        & $MaintenanceScript -RunOnce -Verbose:$Verbose
                    }
                }
                catch {
                    Write-Log "Failed to run maintenance script: $($_.Exception.Message)" "ERROR"
                }
            }
        }
        else {
            $message = "Failed to check model availability: $($result.Error)"
            Write-Log $message "ERROR"
            Send-Alert $message

            # Update metrics for service failure
            foreach ($model in $RequiredModels) {
                Update-ModelMetrics -ModelName $model -Status "SERVICE_ERROR" -HealthDetails @{Error = $result.Error}
            }
        }

        $endTime = Get-Date
        $duration = $endTime - $startTime
        Write-Log "Monitoring cycle #$cycleCount completed in $($duration.TotalSeconds.ToString('F1')) seconds" "INFO"

        Start-Sleep -Seconds $CheckInterval
    }
}

# Handle Ctrl+C gracefully
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Write-Log "Model monitoring stopped by user"
}

# Start monitoring
Start-Monitoring