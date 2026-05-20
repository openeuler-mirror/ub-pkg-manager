#!/bin/bash

source /usr/local/ub-pkg-manager/bin/ub-pkg-common.sh

VIRT_MODULES=(
    "vfio-ub"
    "ubmem_vmmu"
    "ubmempfd"
)


function ub_pkg_virt_main(){
    log INFO "Loading Virt KO modules"
    MODULES=("${DEVICE_MGMT_MODULES[@]}" "${VIRT_MODULES[@]}")
    if ! modprobe_sys_ko "${MODULES[@]}"; then
        log ERROR "Failed to load Virt KO modules, aborting"
        exit 1
    fi
}

ub_pkg_virt_main