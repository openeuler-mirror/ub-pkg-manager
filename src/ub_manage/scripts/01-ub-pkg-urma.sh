#!/bin/bash
source /usr/local/ub-pkg-manager/bin/ub-pkg-common.sh

URMA_MODULES=(
    "ubcore"
    "uburma"
    "ubagg"
    "ipourma"
    "udma"
    "unic"
    "ubl"
)


function ub_pkg_urma_main(){
    log INFO "Loading base and urma KO modules"
    MODULES=("${DEVICE_MGMT_MODULES[@]}" "${URMA_MODULES[@]}")
    if ! modprobe_sys_ko "${MODULES[@]}"; then
        log ERROR "Failed to load base and urma KO modules, aborting"
        exit 1
    fi
}

ub_pkg_urma_main