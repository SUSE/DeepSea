#!/bin/bash
#
# DeepSea integration test "suites/ceph-test/rgw_2_zones.sh"
#
# This script deploys a basic cluster with 2 RGW nodes,
# and after initial deployment, configures 2 rados gateway zones
# in one realm and one zonegroup. After verified RGW configuration,  
# python script is run (python-boto module used) to test:
#  - listing all buckets 
#  - creating a new bucket
#  - creating a new text based object 
#  - reading newly created object  
#
# On success, the script returns 0. On failure, for whatever reason, the script
# returns non-zero.
#
# The script produces verbose output on stdout, which can be captured for later
# forensic analysis.

set -ex
BASEDIR=$(pwd)
source $BASEDIR/common/common.sh
source $BASEDIR/common/rgw.sh

install_deps
cat_salt_config
run_stage_0
run_stage_1
policy_cfg_base
policy_cfg_mon_flex
policy_cfg_rgw 2 
policy_cfg_storage # no node will be a "client"
cat_policy_cfg
run_stage_2
ceph_conf_small_cluster
ceph_conf_mon_allow_pool_delete
run_stage_3
ceph_cluster_status
ceph_health_test
run_stage_4
rgw_configure_2_zones

echo "OK"

