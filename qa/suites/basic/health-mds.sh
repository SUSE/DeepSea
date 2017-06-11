#!/bin/bash -ex
#
# DeepSea integration test "suites/basic/health-mds.sh"
#
# This script runs DeepSea stages 0-4 to deploy a Ceph cluster with MDS.
# After stage 4 completes, it mounts the cephfs on the client node,
# touches a file, and asserts that it exists.
#
# The script makes no assumptions beyond those listed in qa/README.
#
# On success, the script returns 0. On failure, for whatever reason, the script
# returns non-zero.
#
# The script produces verbose output on stdout, which can be captured for later
# forensic analysis.
#
# FIXME:
# - script currently tolerates HEALTH_WARN -> not good. The only HEALTH_WARN
#   outcome it should tolerate is clock skew. (We will need a special ceph.conf
#   for two-node clusters.)
# - In its present form, the test mounts the cephfs on the master node, which
#   is suboptimal because the master node might be running an MDS daemon.
#   The test should be refactored to do the mount on a "client" (non-MDS) node
#   (salt -C 'not I@roles:mds' cmd.run ...)

BASEDIR=$(pwd)
source $BASEDIR/common/common.sh

run_stage_0
run_stage_1
gen_policy_cfg_base
gen_policy_cfg_client
gen_policy_cfg_mds
cat_policy_cfg
run_stage_2
run_stage_3
ceph_health_test
run_stage_4
sleep 10
cephfs_mount_and_sanity_test

echo "OK"
