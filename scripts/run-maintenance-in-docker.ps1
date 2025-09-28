# =============================================================================
# Anclora RAG - Run Maintenance in Docker
# =============================================================================
# This script executes the model maintenance scheduler inside the Docker
# container to ensure proper access to Ollama models.
# =============================================================================

param(
    [switch]$RunOnce = $false,
    [switch]$Verbose = $false
)

# Configuration
$ContainerName = "anclora_rag-ollama-1"
$MaintenanceScript = "/app/scripts/model-maintenance-scheduler.sh"

Write-Host "Anclora RAG - Docker Model Maintenance Runner" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

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

Write-Host "Container $ContainerName is running" -ForegroundColor Green

# Build the command to run inside the container
$command = $MaintenanceScript
if ($RunOnce) {
    $command += " --run-once"
}
if ($Verbose) {
    $command += " --verbose"
}

Write-Host "Executing maintenance script in container..." -ForegroundColor Blue
Write-Host "Command: $command" -ForegroundColor Gray

try {
    # Execute the maintenance script inside the container
    docker exec -it $ContainerName bash -c $command
}
catch {
    Write-Host "Error executing maintenance script: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure the script exists in the container: $MaintenanceScript" -ForegroundColor Yellow
    exit 1
}

Write-Host "Maintenance execution completed" -ForegroundColor Green