#!/bin/bash

source /usr/local/ub-pkg-manager/bin/ub-pkg-common.sh

VIRT_MODULES=(
    "vfio-ub"
)


function ub_pkg_virt_main(){
    log INFO "Loading Virt KO modules"
    if ! modprobe_sys_ko "${VIRT_MODULES[@]}"; then
        log ERROR "Failed to load Virt KO modules, aborting"
        exit 1
    fi
}

ub_pkg_virt_main