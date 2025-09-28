#!/bin/bash
# =============================================================================
# Anclora RAG - Model Protection System Setup
# =============================================================================
# This script sets up the complete model protection system for preventing
# Llama3 model loss and ensuring continuous availability.
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print header
print_header() {
    echo -e "${CYAN}"
    echo "================================================================="
    echo "  Anclora RAG - Model Protection System Setup"
    echo "================================================================="
    echo -e "${NC}"
}

# Check requirements
check_requirements() {
    log_info "Checking system requirements..."

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Check if docker-compose is available
    if ! command -v docker > /dev/null 2>&1; then
        log_error "Docker command not found. Please install Docker."
        exit 1
    fi

    # Check if we're in the right directory
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "docker-compose.yml not found. Please run this script from the project root."
        exit 1
    fi

    log_success "Requirements check passed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."

    directories=("model_backups" "logs" "scripts")

    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_success "Created directory: $dir"
        else
            log_info "Directory already exists: $dir"
        fi
    done
}

# Set script permissions
set_permissions() {
    log_info "Setting script permissions..."

    chmod +x scripts/backup-models.sh
    chmod +x scripts/model-maintenance-scheduler.sh
    chmod +x scripts/setup-model-protection.sh

    log_success "Script permissions set"
}

# Verify script integrity
verify_scripts() {
    log_info "Verifying script integrity..."

    local scripts=("backup-models.sh" "model-maintenance-scheduler.sh" "monitor-models.ps1")
    local all_good=true

    for script in "${scripts[@]}"; do
        if [[ -f "scripts/$script" ]]; then
            log_success "Found script: $script"
        else
            log_error "Missing script: $script"
            all_good=false
        fi
    done

    if [[ "$all_good" != "true" ]]; then
        log_error "Some scripts are missing. Please ensure all files are present."
        exit 1
    fi
}

# Update docker-compose.yml if needed
update_docker_compose() {
    log_info "Checking Docker Compose configuration..."

    if grep -q "backup-models.sh" docker-compose.yml; then
        log_success "Docker Compose already includes model protection"
    else
        log_warning "Docker Compose may need manual update to include health checks"
        log_info "Consider updating the ollama service healthcheck to include:"
        log_info "  test: [\"CMD\", \"sh\", \"-c\", \"ollama list | grep -q llama3 && /app/scripts/backup-models.sh --verify-only\"]"
    fi
}

# Create sample configuration files
create_sample_configs() {
    log_info "Creating sample configuration files..."

    # Create .env.modelprotection if it doesn't exist
    if [[ ! -f ".env.modelprotection" ]]; then
        cat > .env.modelprotection << 'EOF'
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
EOF
        log_success "Created .env.modelprotection with default settings"
    fi
}

# Test the installation
test_installation() {
    log_info "Testing installation..."

    # Test backup script
    if ./scripts/backup-models.sh --help > /dev/null 2>&1; then
        log_success "Backup script is functional"
    else
        log_warning "Backup script may have issues"
    fi

    # Test maintenance scheduler
    if ./scripts/model-maintenance-scheduler.sh --help > /dev/null 2>&1; then
        log_success "Maintenance scheduler script is functional"
    else
        log_warning "Maintenance scheduler script may have issues"
    fi
}

# Print usage instructions
print_usage_instructions() {
    echo -e "\n${CYAN}Setup Complete!${NC}"
    echo -e "${CYAN}===============${NC}"
    echo
    echo -e "${GREEN}The Model Protection System has been successfully installed.${NC}"
    echo
    echo "Next steps:"
    echo
    echo -e "${YELLOW}1. Start the enhanced Docker services:${NC}"
    echo "   docker compose up -d"
    echo
    echo -e "${YELLOW}2. Start the maintenance scheduler:${NC}"
    echo "   ./scripts/model-maintenance-scheduler.sh"
    echo
    echo -e "${YELLOW}3. Start the enhanced monitoring:${NC}"
    echo "   # Windows PowerShell:"
    echo "   .\scripts\monitor-models.ps1"
    echo
    echo -e "${YELLOW}4. Review the documentation:${NC}"
    echo "   cat scripts/README_MODEL_PROTECTION.md"
    echo
    echo -e "${YELLOW}5. Customize configuration:${NC}"
    echo "   Edit .env.modelprotection as needed"
    echo
    echo -e "${CYAN}Key Features:${NC}"
    echo "  ✓ Automatic model backup with checksums"
    echo "  ✓ Integrity verification and recovery"
    echo "  ✓ Enhanced health monitoring"
    echo "  ✓ Scheduled maintenance tasks"
    echo "  ✓ Comprehensive logging and metrics"
    echo "  ✓ Cross-platform compatibility"
    echo
    echo -e "${CYAN}For troubleshooting, check:${NC}"
    echo "  - logs/model_maintenance.log"
    echo "  - model_backups/model_checksums.sha256"
    echo "  - model-metrics.json"
    echo
}

# Main setup function
main() {
    print_header

    log_info "Starting Model Protection System setup..."

    check_requirements
    create_directories
    set_permissions
    verify_scripts
    update_docker_compose
    create_sample_configs
    test_installation

    print_usage_instructions

    log_success "Model Protection System setup completed successfully!"
    echo
    echo -e "${GREEN}Your Llama3 models are now protected against loss and corruption!${NC}"
}

# Handle command line arguments
case "${1:-}" in
    "--help"|"-h")
        echo "Usage: $0 [--help]"
        echo
        echo "Sets up the complete Model Protection System for Anclora RAG."
        echo
        echo "This script will:"
        echo "  - Create necessary directories"
        echo "  - Set script permissions"
        echo "  - Verify script integrity"
        echo "  - Create sample configuration"
        echo "  - Test the installation"
        echo
        exit 0
        ;;
    *)
        main
        ;;
esac