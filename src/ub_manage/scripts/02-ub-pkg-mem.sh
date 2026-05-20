#!/bin/bash

source /usr/local/ub-pkg-manager/bin/ub-pkg-common.sh

MEM_MODULES=(
    "obmm"
    "sentry_remote_reporter"
    "sentry_reporter"
)


function ub_pkg_mem_main(){
    log INFO "Loading Mem KO modules"
    MODULES=("${DEVICE_MGMT_MODULES[@]}" "${MEM_MODULES[@]}")
    if ! modprobe_sys_ko "${MODULES[@]}"; then
        log ERROR "Failed to load Mem KO modules, aborting"
        exit 1
    fi

}

ub_pkg_mem_main