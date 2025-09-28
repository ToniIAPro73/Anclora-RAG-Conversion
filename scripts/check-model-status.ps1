# =============================================================================
# Anclora RAG - Model Status Checker
# =============================================================================
# This script checks the status of Llama3 model and provides basic health
# information without requiring Docker container access.
# =============================================================================

param(
    [switch]$Detailed = $false,
    [switch]$CreateBackup = $false
)

# Configuration
$RequiredModels = @("llama3")
$OllamaHost = "http://localhost:11434"

Write-Host "Anclora RAG - Model Status Checker" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Test Ollama service availability
function Test-OllamaService {
    try {
        $response = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get -TimeoutSec 10
        Write-Host "✓ Ollama service is available" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ Ollama service is not available: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Get model information
function Get-ModelInfo {
    param([string]$ModelName)

    try {
        $response = Invoke-RestMethod -Uri "$OllamaHost/api/show" -Method Post -Body (@{name = $ModelName} | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 30

        $info = @{
            Name = $response.name
            Size = $response.size
            ParameterSize = $response.parameter_size
            QuantizationLevel = $response.quantization_level
            Template = $response.template
            System = $response.system
        }

        return $info
    }
    catch {
        Write-Host "✗ Failed to get details for model $ModelName : $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Main execution
if (Test-OllamaService) {
    Write-Host "`nModel Status Report:" -ForegroundColor Yellow
    Write-Host "===================" -ForegroundColor Yellow

    foreach ($model in $RequiredModels) {
        Write-Host "`nChecking model: $model" -ForegroundColor Blue

        try {
            $response = Invoke-RestMethod -Uri "$OllamaHost/api/tags" -Method Get -TimeoutSec 10
            $modelExists = $response.models | Where-Object { $_.name -like "*$model*" } | Measure-Object | Select-Object -ExpandProperty Count

            if ($modelExists -gt 0) {
                Write-Host "✓ Model $model is available" -ForegroundColor Green

                if ($Detailed) {
                    $modelInfo = Get-ModelInfo -ModelName $model
                    if ($modelInfo) {
                        Write-Host "  Size: $([math]::Round($modelInfo.Size / 1GB, 2)) GB" -ForegroundColor Gray
                        Write-Host "  Parameters: $([math]::Round($modelInfo.ParameterSize / 1GB, 2)) GB" -ForegroundColor Gray
                        Write-Host "  Quantization: $($modelInfo.QuantizationLevel)" -ForegroundColor Gray
                    }
                }

                # Test model functionality
                try {
                    $testResponse = Invoke-RestMethod -Uri "$OllamaHost/api/generate" -Method Post -Body (@{
                        model = $model
                        prompt = "Say 'OK' in one word"
                        stream = $false
                    } | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 120

                    Write-Host "✓ Model $model is functional" -ForegroundColor Green
                }
                catch {
                    Write-Host "⚠ Model $model exists but may have issues: $($_.Exception.Message)" -ForegroundColor Yellow
                }
            }
            else {
                Write-Host "✗ Model $model is missing" -ForegroundColor Red
                Write-Host "  To download: curl -X POST $OllamaHost/api/pull -H 'Content-Type: application/json' -d '{\"name\":\"$model\"}'" -ForegroundColor Gray
            }
        }
        catch {
            Write-Host "✗ Error checking model $model : $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    # Backup information
    if (Test-Path "model_backups") {
        $backupFiles = Get-ChildItem -Path "model_backups" -Name "*.backup" -ErrorAction SilentlyContinue
        if ($backupFiles.Count -gt 0) {
            Write-Host "`nBackup Status:" -ForegroundColor Yellow
            Write-Host "==============" -ForegroundColor Yellow
            Write-Host "✓ Found $($backupFiles.Count) backup file(s)" -ForegroundColor Green
            foreach ($backup in $backupFiles) {
                Write-Host "  - $backup" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "`nBackup Status:" -ForegroundColor Yellow
            Write-Host "==============" -ForegroundColor Yellow
            Write-Host "ℹ No backup files found" -ForegroundColor Gray
        }
    }

    # Log information
    if (Test-Path "logs\model_maintenance.log") {
        $logSize = (Get-Item "logs\model_maintenance.log").Length
        Write-Host "`nLog Status:" -ForegroundColor Yellow
        Write-Host "===========" -ForegroundColor Yellow
        Write-Host "✓ Log file exists ($([math]::Round($logSize / 1KB, 2)) KB)" -ForegroundColor Green
    }
    else {
        Write-Host "`nLog Status:" -ForegroundColor Yellow
        Write-Host "===========" -ForegroundColor Yellow
        Write-Host "ℹ No log file found" -ForegroundColor Gray
    }
}
else {
    Write-Host "`nTroubleshooting Steps:" -ForegroundColor Yellow
    Write-Host "=====================" -ForegroundColor Yellow
    Write-Host "1. Ensure Docker services are running: docker compose up -d" -ForegroundColor Gray
    Write-Host "2. Check if Ollama container is healthy: docker compose ps" -ForegroundColor Gray
    Write-Host "3. Verify model is downloaded: docker exec anclora_rag-ollama-1 ollama list" -ForegroundColor Gray
    Write-Host "4. If model is missing, download it: docker exec anclora_rag-ollama-1 ollama pull llama3" -ForegroundColor Gray
}

Write-Host "`nStatus check completed." -ForegroundColor Green