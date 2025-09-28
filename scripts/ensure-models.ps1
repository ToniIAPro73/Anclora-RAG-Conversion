# =============================================================================
# Anclora RAG - Model Availability Checker (PowerShell)
# =============================================================================
# This script ensures that required models are available in Ollama
# and downloads them if they're missing.
# =============================================================================

param(
    [string]$OllamaHost = "http://localhost:11434",
    [int]$MaxRetries = 5,
    [int]$RetryDelay = 10,
    [switch]$UseDocker = $false
)

# Configuration
$RequiredModels = @("llama3")

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

# Wait for Ollama to be ready
function Wait-ForOllama {
    Write-Info "Waiting for Ollama service to be ready..."
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            if ($UseDocker) {
                $result = docker exec anclora_rag-ollama-1 ollama list 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "Ollama service is ready"
                    return $true
                }
            }
            else {
                $response = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get -TimeoutSec 5
                Write-Success "Ollama service is ready"
                return $true
            }
        }
        catch {
            # Continue to retry
        }
        
        Write-Warning "Ollama not ready, attempt $i/$MaxRetries. Retrying in ${RetryDelay}s..."
        Start-Sleep -Seconds $RetryDelay
    }
    
    Write-Error "Ollama service failed to become ready after $MaxRetries attempts"
    return $false
}

# Check if a model exists
function Test-ModelExists {
    param([string]$ModelName)
    
    try {
        if ($UseDocker) {
            $result = docker exec anclora_rag-ollama-1 ollama list 2>$null
            return $result -match $ModelName
        }
        else {
            $response = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get
            return $response.models | Where-Object { $_.name -eq $ModelName } | Measure-Object | Select-Object -ExpandProperty Count
        }
    }
    catch {
        return $false
    }
}

# Download a model
function Get-Model {
    param([string]$ModelName)
    
    Write-Info "Downloading model: $ModelName"
    
    try {
        if ($UseDocker) {
            $result = docker exec anclora_rag-ollama-1 ollama pull $ModelName
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Model $ModelName downloaded successfully"
                return $true
            }
            else {
                Write-Error "Failed to download model $ModelName via Docker"
                return $false
            }
        }
        else {
            $body = @{ name = $ModelName } | ConvertTo-Json
            $response = Invoke-RestMethod -Uri "$OllamaHost/api/pull" -Method Post -Body $body -ContentType "application/json"
            Write-Success "Model $ModelName downloaded successfully"
            return $true
        }
    }
    catch {
        Write-Error "Failed to download model $ModelName : $($_.Exception.Message)"
        return $false
    }
}

# Main function
function Main {
    Write-Info "Starting Anclora RAG model availability check..."
    
    # Wait for Ollama to be ready
    if (-not (Wait-ForOllama)) {
        exit 1
    }
    
    # Check and download required models
    foreach ($model in $RequiredModels) {
        Write-Info "Checking model: $model"
        
        if (Test-ModelExists -ModelName $model) {
            Write-Success "Model $model is available"
        }
        else {
            Write-Warning "Model $model is missing, downloading..."
            if (-not (Get-Model -ModelName $model)) {
                Write-Error "Failed to ensure model $model is available"
                exit 1
            }
        }
    }
    
    Write-Success "All required models are available!"
    
    # List all available models
    Write-Info "Available models:"
    try {
        $response = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get
        $response.models | ForEach-Object { Write-Host "  - $($_.name)" }
    }
    catch {
        Write-Warning "Unable to list models"
    }
}

# Run main function
Main