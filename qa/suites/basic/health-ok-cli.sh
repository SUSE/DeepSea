#!/bin/bash
#
# DeepSea integration test "suites/basic/health-ok-cli.sh"
#
# This script runs DeepSea stages 0-3 *using the DeepSea CLI* to deploy a Ceph
# cluster on all the nodes that have at least one external disk drive. After
# stage 3 completes, the script checks for HEALTH_OK and dumps the DeepSea 
# log.
#
# The script makes no assumptions beyond those listed in qa/README.
#
# On success (HEALTH_OK is reached), the script returns 0. On failure, for
# whatever reason, the script returns non-zero.
#
# The script produces verbose output on stdout, which can be captured for later
# forensic analysis.
#

set -ex
BASEDIR=$(pwd)
source $BASEDIR/common/common.sh

install_deps
cat_salt_config
run_stage_0 cli
run_stage_1 cli
policy_cfg_base
policy_cfg_no_client
cat_policy_cfg
run_stage_2 cli
ceph_conf_small_cluster
run_stage_3 cli
ceph_cluster_status
ceph_health_test
ceph_version_sanity_test
cat_deepsea_log

echo "OK"
