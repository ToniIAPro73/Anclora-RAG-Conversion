# =============================================================================
# Anclora RAG - Setup Scheduled Task for Model Monitoring
# =============================================================================
# This script creates a Windows Scheduled Task to automatically check
# and ensure model availability.
# =============================================================================

# Requires Administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script requires Administrator privileges. Please run as Administrator."
    exit 1
}

# Configuration
$TaskName = "Anclora-RAG-Model-Check"
$ScriptPath = "$PSScriptRoot\ensure-models.ps1"
$LogPath = "$PSScriptRoot\..\logs\model-check.log"

# Ensure logs directory exists
$LogDir = Split-Path $LogPath -Parent
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force
    Write-Host "Created logs directory: $LogDir" -ForegroundColor Green
}

# Create the scheduled task action
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`" > `"$LogPath`" 2>&1"

# Create triggers
$Triggers = @(
    # Run at system startup (with 2 minute delay)
    New-ScheduledTaskTrigger -AtStartup -RandomDelay (New-TimeSpan -Minutes 2),
    
    # Run every 30 minutes
    New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 365)
)

# Create task settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Create the principal (run as SYSTEM)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the scheduled task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Triggers -Settings $Settings -Principal $Principal -Description "Ensures Anclora RAG models are available in Ollama" -Force
    Write-Host "Successfully created scheduled task: $TaskName" -ForegroundColor Green
    Write-Host "Task will run at startup and every 30 minutes" -ForegroundColor Green
    Write-Host "Logs will be written to: $LogPath" -ForegroundColor Green
}
catch {
    Write-Error "Failed to create scheduled task: $($_.Exception.Message)"
    exit 1
}

# Test the task
Write-Host "Testing the scheduled task..." -ForegroundColor Yellow
try {
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Task started successfully. Check the log file for results." -ForegroundColor Green
}
catch {
    Write-Warning "Failed to start task immediately: $($_.Exception.Message)"
}

Write-Host "`nScheduled task setup complete!" -ForegroundColor Green
Write-Host "You can manage the task using:" -ForegroundColor White
Write-Host "  - Task Scheduler GUI (taskschd.msc)" -ForegroundColor Gray
Write-Host "  - Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  - Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  - Unregister-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray