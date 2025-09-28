#!/bin/bash
# =============================================================================
# Anclora RAG - Model Maintenance Scheduler (Bash)
# =============================================================================
# This script schedules regular model maintenance tasks including integrity
# checks, backups, and recovery operations with detailed logging.
# =============================================================================

set -e

# Configuration
REQUIRED_MODELS=("llama3")
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
LOG_DIR="logs"
LOG_FILE="model_maintenance.log"
INTERVAL_MINUTES=60
MAX_LOG_FILES=10
MAX_LOG_SIZE_MB=100

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global variables
MAINTENANCE_COUNT=0
LOG_PATH="$LOG_DIR/$LOG_FILE"
VERBOSE=false
RUN_ONCE=false

# Logging functions
log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_entry="[$timestamp] [$level] $message"

    # Write to console
    case "$level" in
        "ERROR")
            echo -e "${RED}$log_entry${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}$log_entry${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}$log_entry${NC}"
            ;;
        "INFO")
            if [[ "$VERBOSE" == "true" ]]; then
                echo -e "${BLUE}$log_entry${NC}"
            fi
            ;;
        *)
            if [[ "$VERBOSE" == "true" ]]; then
                echo -e "$log_entry"
            fi
            ;;
    esac

    # Write to log file
    echo "$log_entry" >> "$LOG_PATH"
}

# Initialize logging
initialize_logging() {
    # Create log directory if it doesn't exist
    if [[ ! -d "$LOG_DIR" ]]; then
        mkdir -p "$LOG_DIR"
        log "INFO" "Created log directory: $LOG_DIR"
    fi

    # Rotate log files if necessary
    rotate_log_files

    log "SUCCESS" "Model maintenance scheduler started"
    log "INFO" "Interval: $INTERVAL_MINUTES minutes"
    log "INFO" "Required models: ${REQUIRED_MODELS[*]}"
}

# Rotate log files
rotate_log_files() {
    if [[ -f "$LOG_PATH" ]]; then
        local log_size_mb
        log_size_mb=$(stat -f%z "$LOG_PATH" 2>/dev/null || stat -c%s "$LOG_PATH" 2>/dev/null | awk '{print $1/1024/1024}' 2>/dev/null || echo "0")

        if (( $(echo "$log_size_mb >= $MAX_LOG_SIZE_MB" | bc -l 2>/dev/null) )); then
            # Rotate existing log files
            for ((i = MAX_LOG_FILES - 1; i >= 1; i--)); do
                local old_file="$LOG_DIR/${LOG_FILE}.$i"
                local new_file="$LOG_DIR/${LOG_FILE}.$((i + 1))"
                if [[ -f "$old_file" ]]; then
                    mv "$old_file" "$new_file" 2>/dev/null || true
                fi
            done

            # Move current log to .1
            mv "$LOG_PATH" "$LOG_DIR/${LOG_FILE}.1" 2>/dev/null || true
            log "INFO" "Log file rotated due to size limit (${log_size_mb%.*} MB >= $MAX_LOG_SIZE_MB MB)"
        fi
    fi
}

# Test Ollama service availability
test_ollama_service() {
    if curl -s "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; then
        log "SUCCESS" "Ollama service is available"
        return 0
    else
        log "ERROR" "Ollama service is not available"
        return 1
    fi
}

# Get detailed model information
get_model_details() {
    local model_name="$1"

    local response
    response=$(curl -s -X POST "$OLLAMA_HOST/api/show" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$model_name\"}" 2>/dev/null)

    if [[ $? -eq 0 && $response != "" ]]; then
        log "INFO" "Retrieved details for model $model_name"
        echo "$response"
        return 0
    else
        log "WARNING" "Failed to get details for model $model_name"
        return 1
    fi
}

# Comprehensive model health check
test_model_health() {
    local model_name="$1"
    local health_status="UNKNOWN"

    log "INFO" "Starting comprehensive health check for model: $model_name"

    # 1. Check if model exists in Ollama
    if curl -s "$OLLAMA_HOST/api/tags" | grep -q "\"name\":\"$model_name"; then
        log "INFO" "Model exists check: true"
        local model_exists=true
    else
        log "INFO" "Model exists check: false"
        local model_exists=false
    fi

    # 2. Get model details
    if [[ "$model_exists" == "true" ]]; then
        if details=$(get_model_details "$model_name"); then
            local details_retrieved=true

            # 3. Test model loading
            if curl -s -X POST "$OLLAMA_HOST/api/generate" \
                -H "Content-Type: application/json" \
                -d "{\"model\":\"$model_name\",\"prompt\":\"test\",\"stream\":false}" \
                > /dev/null 2>&1; then
                log "SUCCESS" "Model loading test passed"
                local model_loads=true
            else
                log "ERROR" "Model loading test failed"
                local model_loads=false
            fi
        else
            local details_retrieved=false
        fi
    else
        local details_retrieved=false
        local model_loads=false
    fi

    # 4. Run backup integrity check
    if [[ -f "scripts/backup-models.sh" ]]; then
        if ./scripts/backup-models.sh --verify-only > /dev/null 2>&1; then
            log "INFO" "Integrity verification: true"
            local integrity_verified=true
        else
            log "ERROR" "Integrity verification: false"
            local integrity_verified=false
        fi
    else
        log "WARNING" "Backup script not found: scripts/backup-models.sh"
        local integrity_verified=false
    fi

    # Determine overall status
    if [[ "$model_exists" == "true" && "$details_retrieved" == "true" && "$model_loads" == "true" && "$integrity_verified" == "true" ]]; then
        health_status="HEALTHY"
        log "INFO" "Overall health status for $model_name: HEALTHY"
    else
        health_status="UNHEALTHY"
        log "WARNING" "Overall health status for $model_name: UNHEALTHY"
    fi

    echo "$health_status"
}

# Perform maintenance actions
perform_maintenance() {
    local model_name="$1"
    local actions=()

    log "INFO" "Performing maintenance for model: $model_name"

    # 1. Run backup script
    if [[ -f "scripts/backup-models.sh" ]]; then
        if ./scripts/backup-models.sh > /dev/null 2>&1; then
            actions+=("Backup completed")
            log "SUCCESS" "Backup completed successfully"
        else
            actions+=("Backup failed")
            log "ERROR" "Backup failed"
        fi
    fi

    # 2. Clean old backups
    if [[ -d "model_backups" ]]; then
        local old_backups
        mapfile -t old_backups < <(ls -t "model_backups/${model_name}_"*.backup 2>/dev/null | tail -n +6)
        for backup in "${old_backups[@]}"; do
            rm -f "$backup" "${backup%.backup}.sha256" 2>/dev/null || true
        done
        actions+=("Old backups cleaned")
        log "INFO" "Old backups cleaned"
    fi

    echo "${actions[*]}"
}

# Main maintenance cycle
maintenance_cycle() {
    ((MAINTENANCE_COUNT++))

    log "INFO" "=== Starting maintenance cycle #$MAINTENANCE_COUNT ==="

    # Check Ollama service
    if ! test_ollama_service; then
        log "WARNING" "Skipping maintenance cycle due to Ollama service unavailability"
        return
    fi

    local healthy_count=0

    # Process each model
    for model in "${REQUIRED_MODELS[@]}"; do
        log "INFO" "Processing model: $model"

        # Health check
        if [[ "$(test_model_health "$model")" == "HEALTHY" ]]; then
            ((healthy_count++))
            log "INFO" "Model $model is healthy, skipping maintenance"
        else
            log "WARNING" "Model $model is unhealthy, performing maintenance"
            perform_maintenance "$model" > /dev/null
        fi
    done

    local total_models=${#REQUIRED_MODELS[@]}
    log "SUCCESS" "Maintenance cycle #$MAINTENANCE_COUNT completed - $healthy_count/$total_models models healthy"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --interval)
                INTERVAL_MINUTES="$2"
                shift 2
                ;;
            --run-once)
                RUN_ONCE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                echo "Usage: $0 [--interval MINUTES] [--run-once] [--verbose]"
                exit 0
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

# Main function
main() {
    echo -e "${CYAN}Anclora RAG Model Maintenance Scheduler${NC}"
    echo -e "${CYAN}======================================${NC}"

    parse_args "$@"

    # Initialize logging
    initialize_logging

    if [[ "$RUN_ONCE" == "true" ]]; then
        # Run once and exit
        maintenance_cycle
    else
        # Continuous monitoring
        log "INFO" "Starting continuous maintenance schedule (interval: $INTERVAL_MINUTES minutes)"

        while true; do
            local start_time
            start_time=$(date +%s)
            maintenance_cycle
            local end_time
            end_time=$(date +%s)

            local duration=$((end_time - start_time))
            log "INFO" "Maintenance cycle completed in ${duration}s"

            # Wait for next cycle
            local wait_time=$((INTERVAL_MINUTES * 60 - duration))
            if (( wait_time > 0 )); then
                sleep "$wait_time"
            fi
        done
    fi
}

# Handle signals gracefully
trap 'log "WARNING" "Model maintenance scheduler stopped by signal"; exit 0' INT TERM

# Run main function with all arguments
main "$@"