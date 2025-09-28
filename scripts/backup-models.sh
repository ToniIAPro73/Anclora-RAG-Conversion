#!/bin/bash
# =============================================================================
# Anclora RAG - Model Backup and Integrity System (Bash)
# =============================================================================
# This script creates backups of Ollama models with checksums for integrity
# verification and automatic recovery.
# =============================================================================

set -e

# Configuration
REQUIRED_MODELS=("llama3")
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
BACKUP_DIR="model_backups"
MAX_RETRIES=3
RETRY_DELAY=5
CHECKSUM_FILE="$BACKUP_DIR/model_checksums.sha256"

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

# Create backup directory
initialize_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        log_info "Created backup directory: $BACKUP_DIR"
    fi
}

# Get model file path
get_model_path() {
    local model_name="$1"

    # For Docker environment, models are typically in /root/.ollama/models
    local ollama_dir="/root/.ollama"
    local model_path="$ollama_dir/models"

    if [[ -d "$model_path" ]]; then
        echo "$model_path"
        return 0
    fi

    log_warning "Could not determine model path for $model_name"
    return 1
}

# Calculate file checksum
get_file_checksum() {
    local file_path="$1"

    if command -v sha256sum &> /dev/null; then
        sha256sum "$file_path" | cut -d' ' -f1
    elif command -v shasum &> /dev/null; then
        shasum -a 256 "$file_path" | cut -d' ' -f1
    else
        log_error "No checksum utility available (sha256sum or shasum)"
        return 1
    fi
}

# Save checksums to file
save_checksums() {
    local -n checksums_ref=$1

    > "$CHECKSUM_FILE"
    for model in "${!checksums_ref[@]}"; do
        echo "${checksums_ref[$model]}  $model" >> "$CHECKSUM_FILE"
    done
    log_info "Checksums saved to: $CHECKSUM_FILE"
}

# Load existing checksums
load_checksums() {
    declare -A checksums=()

    if [[ -f "$CHECKSUM_FILE" ]]; then
        while IFS=' ' read -r checksum model; do
            checksums[$model]="$checksum"
        done < "$CHECKSUM_FILE"
    fi

    echo "Checksums loaded: ${#checksums[@]} models"
}

# Verify model integrity
test_model_integrity() {
    local model_name="$1"
    log_info "Verifying integrity of model: $model_name"

    local model_path
    model_path=$(get_model_path "$model_name")
    if [[ $? -ne 0 ]]; then
        return 1
    fi

    # Find model files (typically .bin files)
    local model_files=($(find "$model_path" -name "*${model_name}*" -type f))

    if [[ ${#model_files[@]} -eq 0 ]]; then
        log_warning "No model files found for $model_name"
        return 1
    fi

    # Check the largest file (usually the main model file)
    local largest_file=""
    local largest_size=0

    for file in "${model_files[@]}"; do
        local size
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        if [[ $size -gt $largest_size ]]; then
            largest_size=$size
            largest_file="$file"
        fi
    done

    if [[ -z "$largest_file" ]]; then
        log_error "Could not find model file for $model_name"
        return 1
    fi

    local current_checksum
    current_checksum=$(get_file_checksum "$largest_file")
    if [[ $? -ne 0 ]]; then
        return 1
    fi

    # Load existing checksums
    declare -A existing_checksums
    eval "$(load_checksums)"

    local expected_checksum="${existing_checksums[$model_name]}"

    if [[ -n "$expected_checksum" && "$current_checksum" == "$expected_checksum" ]]; then
        log_success "Model $model_name integrity verified"
        return 0
    else
        log_warning "Model $model_name integrity check failed"
        return 1
    fi
}

# Create model backup
backup_model() {
    local model_name="$1"
    log_info "Creating backup for model: $model_name"

    local model_path
    model_path=$(get_model_path "$model_name")
    if [[ $? -ne 0 ]]; then
        log_error "Cannot backup model $model_name - path not found"
        return 1
    fi

    local timestamp
    timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$BACKUP_DIR/${model_name}_${timestamp}.backup"
    local checksum_file="$BACKUP_DIR/${model_name}_${timestamp}.sha256"

    # Find model files to backup
    local model_files=($(find "$model_path" -name "*${model_name}*" -type f))

    if [[ ${#model_files[@]} -eq 0 ]]; then
        log_error "No model files found for $model_name"
        return 1
    fi

    # Create tar backup of all model files
    if tar -czf "$backup_file" -C "$model_path" "${model_files[@]##*/}" 2>/dev/null; then
        log_success "Model backup created: $backup_file"

        # Calculate and save checksum
        local checksum
        checksum=$(get_file_checksum "$backup_file")
        if [[ $? -eq 0 ]]; then
            echo "$checksum" > "$checksum_file"
            log_success "Checksum saved: $checksum_file"

            # Update master checksums file
            declare -A checksums
            eval "$(load_checksums)"
            checksums[$model_name]="$checksum"
            save_checksums checksums
        fi

        return 0
    else
        log_error "Failed to create backup for model $model_name"
        return 1
    fi
}

# Restore model from backup
restore_model() {
    local model_name="$1"
    log_info "Restoring model from backup: $model_name"

    # Find latest backup
    local backup_files
    mapfile -t backup_files < <(ls -t "$BACKUP_DIR/${model_name}_"*.backup 2>/dev/null | head -1)

    if [[ ${#backup_files[@]} -eq 0 ]]; then
        log_error "No backup found for model $model_name"
        return 1
    fi

    local latest_backup="${backup_files[0]}"
    log_info "Restoring from: $latest_backup"

    local model_path
    model_path=$(get_model_path "$model_name")
    if [[ $? -ne 0 ]]; then
        log_error "Cannot restore model $model_name - destination path not found"
        return 1
    fi

    # Extract backup
    if tar -xzf "$latest_backup" -C "$model_path" 2>/dev/null; then
        log_success "Model $model_name restored from: $latest_backup"

        # Verify integrity after restore
        if test_model_integrity "$model_name"; then
            log_success "Model integrity verified after restore"
            return 0
        else
            log_warning "Model integrity check failed after restore"
            return 1
        fi
    else
        log_error "Failed to restore model $model_name"
        return 1
    fi
}

# Clean old backups
clear_old_backups() {
    local keep_last=${1:-5}
    log_info "Cleaning old backups (keeping last $keep_last)"

    for model in "${REQUIRED_MODELS[@]}"; do
        local backup_files
        mapfile -t backup_files < <(ls -t "$BACKUP_DIR/${model}_"*.backup 2>/dev/null)

        if [[ ${#backup_files[@]} -gt $keep_last ]]; then
            local files_to_delete=("${backup_files[@]:$keep_last}")

            for file in "${files_to_delete[@]}"; do
                rm -f "$file" "${file%.backup}.sha256"
                log_info "Removed old backup: $file"
            done
        fi
    done
}

# Verify only mode (for healthchecks)
verify_only() {
    for model in "${REQUIRED_MODELS[@]}"; do
        if ! test_model_integrity "$model"; then
            return 1
        fi
    done
    return 0
}

# Main function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verify-only)
                verify_only
                exit $?
                ;;
            --help)
                echo "Usage: $0 [--verify-only]"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    log_info "Starting Anclora RAG model backup and integrity system..."

    # Initialize backup directory
    initialize_backup_dir

    # Process each required model
    for model in "${REQUIRED_MODELS[@]}"; do
        log_info "Processing model: $model"

        # Check if model exists
        if curl -s "$OLLAMA_HOST/api/tags" | grep -q "\"name\":\"$model"; then
            # Verify model integrity
            if test_model_integrity "$model"; then
                log_success "Model $model is healthy"
            else
                log_warning "Model $model integrity check failed"

                # Try to restore from backup
                if restore_model "$model"; then
                    log_success "Model $model restored from backup"
                else
                    log_error "Failed to restore model $model from backup"
                    # Try to re-download the model
                    log_info "Attempting to re-download model $model"
                    if curl -X POST "$OLLAMA_HOST/api/pull" \
                        -H "Content-Type: application/json" \
                        -d "{\"name\":\"$model\"}" \
                        --no-progress-meter; then
                        log_success "Model $model re-downloaded successfully"
                    else
                        log_error "Failed to re-download model $model"
                    fi
                fi
            fi
        else
            log_warning "Model $model not found, skipping backup"
        fi
    done

    # Clean old backups
    clear_old_backups 5

    log_success "Model backup and integrity system completed!"
}

# Run main function with all arguments
main "$@"