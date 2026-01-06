#!/bin/bash

source /usr/local/ub-pkg-manager/bin/ub-pkg-common.sh

MEM_MODULES=(
    "obmm"
)


function ub_pkg_mem_main(){
    log INFO "Loading Mem KO modules"
    if ! modprobe_sys_ko "${MEM_MODULES[@]}"; then
        log ERROR "Failed to load Mem KO modules, aborting"
        exit 1
    fi

    if [ -f "/lib/modules/$(uname -r)/kernel/drivers/sentry_reporter.ko" ] ; then
        modprobe sentry_reporter
        modprobe sentry_remote_reporter
    else
        log WARN "Not found sentry_reporter module file, skipping"
        exit 1
fi
}

ub_pkg_mem_main