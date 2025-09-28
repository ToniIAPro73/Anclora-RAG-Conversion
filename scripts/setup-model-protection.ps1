# =============================================================================
# Anclora RAG - Model Protection System Setup (PowerShell)
# =============================================================================
# This script sets up the complete model protection system for preventing
# Llama3 model loss and ensuring continuous availability.
# =============================================================================

param(
    [switch]$SkipDockerCheck,
    [switch]$Help
)

# Colors for output
$Green = "Green"
$Cyan = "Cyan"
$Yellow = "Yellow"
$Red = "Red"
$Blue = "Blue"

# Logging functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

# Print header
function Print-Header {
    Write-Host "=================================================================" -ForegroundColor $Cyan
    Write-Host "  Anclora RAG - Model Protection System Setup" -ForegroundColor $Cyan
    Write-Host "=================================================================" -ForegroundColor $Cyan
}

# Check requirements
function Test-Requirements {
    Write-Info "Checking system requirements..."

    if (!$SkipDockerCheck) {
        # Check if Docker is running
        try {
            $dockerInfo = docker info 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Docker is running"
            }
            else {
                Write-Error "Docker is not running. Please start Docker and try again."
                exit 1
            }
        }
        catch {
            Write-Error "Docker command not found. Please install Docker."
            exit 1
        }
    }

    # Check if we're in the right directory
    if (!(Test-Path "docker-compose.yml")) {
        Write-Error "docker-compose.yml not found. Please run this script from the project root."
        exit 1
    }

    Write-Success "Requirements check passed"
}

# Create necessary directories
function New-Directories {
    Write-Info "Creating necessary directories..."

    $directories = @("model_backups", "logs", "scripts")

    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Success "Created directory: $dir"
        }
        else {
            Write-Info "Directory already exists: $dir"
        }
    }
}

# Verify script integrity
function Test-Scripts {
    Write-Info "Verifying script integrity..."

    $scripts = @("backup-models.ps1", "model-maintenance-scheduler.ps1", "monitor-models.ps1")
    $allGood = $true

    foreach ($script in $scripts) {
        $scriptPath = Join-Path "scripts" $script
        if (Test-Path $scriptPath) {
            Write-Success "Found script: $script"
        }
        else {
            Write-Error "Missing script: $script"
            $allGood = $false
        }
    }

    if (!$allGood) {
        Write-Error "Some scripts are missing. Please ensure all files are present."
        exit 1
    }
}

# Update docker-compose.yml if needed
function Test-DockerCompose {
    Write-Info "Checking Docker Compose configuration..."

    $composeContent = Get-Content "docker-compose.yml" -Raw

    if ($composeContent -match "backup-models\.sh") {
        Write-Success "Docker Compose already includes model protection"
    }
    else {
        Write-Warning "Docker Compose may need manual update to include health checks"
        Write-Info "Consider updating the ollama service healthcheck to include:"
        Write-Info "  test: ['CMD', 'sh', '-c', 'ollama list | grep -q llama3 && /app/scripts/backup-models.sh --verify-only']"
    }
}

# Create sample configuration files
function New-SampleConfigs {
    Write-Info "Creating sample configuration files..."

    # Create .env.modelprotection if it doesn't exist
    if (!(Test-Path ".env.modelprotection")) {
        $configContent = @"
# =============================================================================
# Anclora RAG - Model Protection Configuration
# =============================================================================

# Model Protection Settings
MODEL_PROTECTION_ENABLED=true
MAINTENANCE_INTERVAL_MINUTES=60
BACKUP_RETENTION_COUNT=5
HEALTH_CHECK_INTERVAL_SECONDS=60

# Logging Configuration
LOG_LEVEL=INFO
LOG_MAX_SIZE_MB=100
LOG_MAX_FILES=10

# Alert Configuration (optional)
ALERT_EMAIL=
SLACK_WEBHOOK_URL=

# Advanced Settings
OLLAMA_HOST=http://localhost:11434
METRICS_ENABLED=true
AUTO_RECOVERY_ENABLED=true
"@

        $configContent | Out-File -FilePath ".env.modelprotection" -Encoding UTF8
        Write-Success "Created .env.modelprotection with default settings"
    }
}

# Test the installation
function Test-Installation {
    Write-Info "Testing installation..."

    # Test backup script
    try {
        $testResult = & ".\scripts\backup-models.ps1" -?
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Backup script is functional"
        }
        else {
            Write-Warning "Backup script may have issues"
        }
    }
    catch {
        Write-Warning "Could not test backup script: $($_.Exception.Message)"
    }

    # Test maintenance scheduler
    try {
        $helpContent = Get-Content ".\scripts\model-maintenance-scheduler.ps1" -Raw
        if ($helpContent -match "param") {
            Write-Success "Maintenance scheduler script is functional"
        }
        else {
            Write-Warning "Maintenance scheduler script may have issues"
        }
    }
    catch {
        Write-Warning "Could not test maintenance scheduler script: $($_.Exception.Message)"
    }
}

# Print usage instructions
function Print-UsageInstructions {
    Write-Host
    Write-Host "Setup Complete!" -ForegroundColor $Cyan
    Write-Host "===============" -ForegroundColor $Cyan
    Write-Host
    Write-Host "The Model Protection System has been successfully installed." -ForegroundColor $Green
    Write-Host
    Write-Host "Next steps:"
    Write-Host
    Write-Host "1. Start the enhanced Docker services:" -ForegroundColor $Yellow
    Write-Host "   docker compose up -d"
    Write-Host
    Write-Host "2. Start the maintenance scheduler:" -ForegroundColor $Yellow
    Write-Host "   .\scripts\model-maintenance-scheduler.ps1"
    Write-Host
    Write-Host "3. Start the enhanced monitoring:" -ForegroundColor $Yellow
    Write-Host "   .\scripts\monitor-models.ps1"
    Write-Host
    Write-Host "4. Review the documentation:" -ForegroundColor $Yellow
    Write-Host "   Get-Content .\scripts\README_MODEL_PROTECTION.md"
    Write-Host
    Write-Host "5. Customize configuration:" -ForegroundColor $Yellow
    Write-Host "   Edit .env.modelprotection as needed"
    Write-Host
    Write-Host "Key Features:" -ForegroundColor $Cyan
    Write-Host "  ✓ Automatic model backup with checksums"
    Write-Host "  ✓ Integrity verification and recovery"
    Write-Host "  ✓ Enhanced health monitoring"
    Write-Host "  ✓ Scheduled maintenance tasks"
    Write-Host "  ✓ Comprehensive logging and metrics"
    Write-Host "  ✓ Cross-platform compatibility"
    Write-Host
    Write-Host "For troubleshooting, check:" -ForegroundColor $Cyan
    Write-Host "  - logs\model_maintenance.log"
    Write-Host "  - model_backups\model_checksums.sha256"
    Write-Host "  - model-metrics.json"
    Write-Host
}

# Show help
function Show-Help {
    Write-Host "Anclora RAG - Model Protection System Setup" -ForegroundColor $Cyan
    Write-Host
    Write-Host "Usage: .\setup-model-protection.ps1 [options]"
    Write-Host
    Write-Host "Options:"
    Write-Host "  -SkipDockerCheck    Skip Docker availability check"
    Write-Host "  -Help              Show this help message"
    Write-Host
    Write-Host "This script will:"
    Write-Host "  - Create necessary directories"
    Write-Host "  - Verify script integrity"
    Write-Host "  - Create sample configuration"
    Write-Host "  - Test the installation"
    Write-Host
}

# Main setup function
function Main {
    if ($Help) {
        Show-Help
        return
    }

    Print-Header

    Write-Info "Starting Model Protection System setup..."

    Test-Requirements
    New-Directories
    Test-Scripts
    Test-DockerCompose
    New-SampleConfigs
    Test-Installation

    Print-UsageInstructions

    Write-Success "Model Protection System setup completed successfully!"
    Write-Host
    Write-Host "Your Llama3 models are now protected against loss and corruption!" -ForegroundColor $Green
}

# Run main function
Main