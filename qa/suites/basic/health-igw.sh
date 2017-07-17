#!/bin/bash
#
# DeepSea integration test "suites/basic/health-igw.sh"
#
# This script runs DeepSea stages 0-4 to deploy a Ceph cluster with an "igw"
# role configured. After stage 4 completes, it mounts the iSCSI demo image on
# the client node, touches a file, and asserts that it exists.
#
# The script makes no assumptions beyond those listed in qa/README.
#
# On success, the script returns 0. On failure, for whatever reason, the script
# returns non-zero.
#
# The script produces verbose output on stdout, which can be captured for later
# forensic analysis.
#

set -ex
BASEDIR=$(pwd)
source $BASEDIR/common/common.sh

install_deps
cat_salt_config
run_stage_0
run_stage_1
policy_cfg_base
policy_cfg_client
policy_cfg_igw
cat_policy_cfg
run_stage_2
ceph_conf_small_cluster
run_stage_3
ceph_cluster_status
run_stage_4
ceph_cluster_status
ceph_health_test
iscsi_mount_and_sanity_test

echo "OK"
