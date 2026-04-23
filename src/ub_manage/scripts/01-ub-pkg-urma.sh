#!/bin/bash
source /usr/local/ub-pkg-manager/bin/ub-pkg-common.sh

URMA_MODULES=(
    "ubfi"
    "ummu_core"
    "ummu"
    "ubus"
    "hisi_ubus"
    "cdma"
    "ummu_pmu"
    "ub_fwctl"
    "cis"
    "odf"
    "ubase"
    "ubl"
    "unic"
    "ubcore"
    "uburma"
    "udma"
    "ubagg"
    "ipourma"
)


function ub_pkg_urma_main(){
    log INFO "Loading base and urma KO modules"
    if ! modprobe_sys_ko "${URMA_MODULES[@]}"; then
        log ERROR "Failed to load base and urma KO modules, aborting"
        exit 1
    fi
}

ub_pkg_urma_main