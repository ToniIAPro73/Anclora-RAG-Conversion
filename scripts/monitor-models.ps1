# =============================================================================
# Anclora RAG - Continuous Model Monitor
# =============================================================================
# This script continuously monitors model availability and sends alerts
# if models become unavailable.
# =============================================================================

param(
    [int]$CheckInterval = 300, # 5 minutes
    [string]$LogFile = "model-monitor.log",
    [switch]$SendAlerts = $false
)

# Configuration
$RequiredModels = @("llama3")
$OllamaHost = "http://localhost:11434"

# Logging function
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Write to console
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        default { Write-Host $logEntry -ForegroundColor White }
    }
    
    # Write to log file
    Add-Content -Path $LogFile -Value $logEntry
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

# Main monitoring loop
function Start-Monitoring {
    Write-Log "Starting Anclora RAG model monitoring..."
    Write-Log "Check interval: $CheckInterval seconds"
    Write-Log "Required models: $($RequiredModels -join ', ')"
    
    while ($true) {
        $result = Test-ModelAvailability
        
        if ($result.Success) {
            if ($result.MissingModels.Count -eq 0) {
                Write-Log "All required models are available: $($result.AvailableModels -join ', ')" "SUCCESS"
            }
            else {
                $message = "Missing models detected: $($result.MissingModels -join ', ')"
                Write-Log $message "WARNING"
                Send-Alert $message
                
                # Attempt to trigger model download
                Write-Log "Attempting to trigger model download via ensure-models script..."
                try {
                    & "$PSScriptRoot\ensure-models.ps1"
                }
                catch {
                    Write-Log "Failed to run ensure-models script: $($_.Exception.Message)" "ERROR"
                }
            }
        }
        else {
            $message = "Failed to check model availability: $($result.Error)"
            Write-Log $message "ERROR"
            Send-Alert $message
        }
        
        Start-Sleep -Seconds $CheckInterval
    }
}

# Handle Ctrl+C gracefully
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Write-Log "Model monitoring stopped by user"
}

# Start monitoring
Start-Monitoring