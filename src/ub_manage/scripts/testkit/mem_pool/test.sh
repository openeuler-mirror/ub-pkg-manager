#!/bin/bash

yum install -y gcc
gcc /usr/local/ub-pkg-manager/bin/testkit/mem_pool/test_export.c -o /usr/local/ub-pkg-manager/bin/testkit/mem_pool/test_export -lobmm
gcc /usr/local/ub-pkg-manager/bin/testkit/mem_pool/test_unexport.c -o /usr/local/ub-pkg-manager/bin/testkit/mem_pool/test_unexport -lobmm

export_mem=${1:-"128"}

MB2B=$((1024 * 1024))
CNA_PATH="/sys/devices/ub_bus_controller0/00001/primary_cna"
EID_PATH="/sys/devices/ub_bus_controller0/00001/eid"
SYS_SHMDEV='/sys/devices/obmm/obmm_shmdev'

ECNA=$(cat ${CNA_PATH})
DEID=$(cat ${EID_PATH})

/usr/local/ub-pkg-manager/bin/testkit/mem_pool/test_export $((export_mem * MB2B)) 1 $DEID &> export.log || exit 1
cat export.log

mem_id=$(grep -oP 'mem_id=\K\d+' export.log | head -1)
if [ -n "$mem_id" ]; then
	/usr/local/ub-pkg-manager/bin/testkit/mem_pool/test_unexport "$mem_id" || exit 1
else
	echo "ERROR: failed to found mem_id"
	exit 1
fi
