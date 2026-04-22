#!/bin/bash

source /usr/local/ub-pkg-manager/bin/ub-pkg-common.sh

MEM_MODULES=(
    "obmm"
    "ubdevshm"
)

SENTRY_MODULES=(
    "sentry_reporter"
    "sentry_remote_reporter"
)

function ub_pkg_mem_main(){
    log INFO "Loading Mem KO modules"
    if ! modprobe_sys_ko "${MEM_MODULES[@]}"; then
        log ERROR "Failed to load Mem KO modules, aborting"
        exit 1
    fi

    if ! modprobe_sys_ko "${SENTRY_MODULES[@]}"; then
        log WARN "Failed to load SENTRY KO modules, skipping"
        exit 0
    fi
}

ub_pkg_mem_main