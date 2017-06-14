#!/bin/bash -ex
#
# DeepSea integration test "suites/basic/health-nfs-ganesha.sh"
#
# This script runs DeepSea stages 0-4 to deploy a Ceph cluster with MDS and
# NFS-Ganesha.  After stage 4 completes, it mounts the NFS-Ganesha on the
# client node, touches a file, and asserts that it exists.
#
# The script makes no assumptions beyond those listed in qa/README.
#
# On success, the script returns 0. On failure, for whatever reason, the script
# returns non-zero.
#
# The script produces verbose output on stdout, which can be captured for later
# forensic analysis.
#

BASEDIR=$(pwd)
source $BASEDIR/common/common.sh
source $BASEDIR/common/nfs-ganesha.sh

#nfs_ganesha_no_grace_period
run_stage_0
run_stage_1
policy_cfg_base
policy_cfg_client
policy_cfg_mds
policy_cfg_nfs_ganesha
cat_policy_cfg
run_stage_2
ceph_conf
run_stage_3
nfs_ganesha_no_root_squash
run_stage_4
ceph_health_test
nfs_ganesha_cat_config_file
nfs_ganesha_debug_log
nfs_ganesha_showmount_loop
nfs_ganesha_mount
nfs_ganesha_touch_a_file

echo "OK"
