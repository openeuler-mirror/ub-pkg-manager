#!/bin/bash

source /usr/local/ub-pkg-manager/bin/ub-pkg-common.sh

MEM_MODULES=(
    "obmm"
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

    if [ ! -f "/lib/modules/$(uname -r)/kernel/drivers/ub/sentry/sentry_reporter.ko" ]; then
        log WARN "Not found sentry_reporter module file, skipping"
        exit 0
    elif ! modprobe_sys_ko "${SENTRY_MODULES[@]}"; then
        log ERROR "Failed to load SENTRY KO modules, aborting"
        exit 1
    fi
}

ub_pkg_mem_main