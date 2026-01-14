#!/bin/bash

LOG_FILE="/var/log/ub-pkg-manager.log"
LOG_LEVEL="INFO"

ensure_log_dir() {
    local log_dir="$1"
    
    if [ -z "$log_dir" ]; then
        log_dir="$(dirname "$LOG_FILE")"
    fi
    
    if [ ! -d "$log_dir" ]; then
        mkdir -p "$log_dir" 2>/dev/null || {
            echo "ERROR: Failed to create log directory $log_dir" >&2
            exit 1
        }
    fi
    
    touch "$LOG_FILE" 2>/dev/null || {
        echo "ERROR: Failed to create log file $LOG_FILE" >&2
        exit 1
    }
    chmod 644 "$LOG_FILE" 2>/dev/null || {
        echo "WARNING: Failed to set permissions for log file $LOG_FILE" >&2
    }
}

log() {
    local level="$1"
    shift
    local message="$@"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    local script_name="$(basename "$0")"
    
    # Only log if level is >= current LOG_LEVEL
    local level_order=("DEBUG" "INFO" "WARN" "ERROR")
    local current_level_index=-1
    local message_level_index=-1
    
    for i in "${!level_order[@]}"; do
        if [ "${level_order[$i]}" == "$LOG_LEVEL" ]; then
            current_level_index=$i
        fi
        if [ "${level_order[$i]}" == "$level" ]; then
            message_level_index=$i
        fi
    done
    
    if [ $message_level_index -ge $current_level_index ] || [ $current_level_index -eq -1 ]; then
        echo "$timestamp [$level] $script_name: $message" >> "$LOG_FILE"
    fi
}

module_is_loaded() {
    lsmod | grep -q "^$1\b " >/dev/null 2>&1
}

run_step() {
    local desc="$1"
    shift
    local cmd="$@"
    local script_name="$(basename "$0")"
    
    log INFO "Starting: $desc"
    log DEBUG "Command: $cmd"
    
    if out=$($cmd 2>&1); then
        log INFO "Success: $desc"
        log DEBUG "Output: $out"
        return 0
    else
        local exit_code=$?
        log ERROR "Failed: $desc (exit code: $exit_code)"
        log ERROR "Command output: $out"
        return $exit_code
    fi
}

modprobe_sys_ko() {
    ko=($@)
    
    for mod in "${ko[@]}"; do
        if ! module_is_loaded "$mod"; then
            if ! run_step "modprobe $mod" modprobe "$mod"; then
                log ERROR "Failed to load module $mod, aborting"
                return 1
            fi
        else
            log INFO "Module $mod is already loaded, skipping"
        fi
    done
    
    log INFO "All KO modules loaded successfully"
    return 0
}

check_ubrt_support() {
    if [ ! -f "/sys/firmware/acpi/tables/UBRT" ]; then
        log ERROR "The ACPI table UBRT is not found, current system does not support UB."
        exit 1
    fi
}

ensure_log_dir
check_ubrt_support

