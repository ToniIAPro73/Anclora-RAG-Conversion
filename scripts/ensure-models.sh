#!/bin/bash
# =============================================================================
# Anclora RAG - Model Availability Checker
# =============================================================================
# This script ensures that required models are available in Ollama
# and downloads them if they're missing.
# =============================================================================

set -e

# Configuration
REQUIRED_MODELS=("llama3")
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
MAX_RETRIES=5
RETRY_DELAY=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Wait for Ollama to be ready
wait_for_ollama() {
    log_info "Waiting for Ollama service to be ready..."
    
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -s "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; then
            log_success "Ollama service is ready"
            return 0
        fi
        
        log_warning "Ollama not ready, attempt $i/$MAX_RETRIES. Retrying in ${RETRY_DELAY}s..."
        sleep $RETRY_DELAY
    done
    
    log_error "Ollama service failed to become ready after $MAX_RETRIES attempts"
    return 1
}

# Check if a model exists
model_exists() {
    local model_name="$1"
    curl -s "$OLLAMA_HOST/api/tags" | grep -q "\"name\":\"$model_name"
}

# Download a model
download_model() {
    local model_name="$1"
    log_info "Downloading model: $model_name"
    
    curl -X POST "$OLLAMA_HOST/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$model_name\"}" \
        --no-progress-meter
    
    if [ $? -eq 0 ]; then
        log_success "Model $model_name downloaded successfully"
    else
        log_error "Failed to download model $model_name"
        return 1
    fi
}

# Main function
main() {
    log_info "Starting Anclora RAG model availability check..."
    
    # Wait for Ollama to be ready
    if ! wait_for_ollama; then
        exit 1
    fi
    
    # Check and download required models
    for model in "${REQUIRED_MODELS[@]}"; do
        log_info "Checking model: $model"
        
        if model_exists "$model"; then
            log_success "Model $model is available"
        else
            log_warning "Model $model is missing, downloading..."
            if ! download_model "$model"; then
                log_error "Failed to ensure model $model is available"
                exit 1
            fi
        fi
    done
    
    log_success "All required models are available!"
    
    # List all available models
    log_info "Available models:"
    curl -s "$OLLAMA_HOST/api/tags" | jq -r '.models[].name' 2>/dev/null || echo "Unable to list models"
}

# Run main function
main "$@"