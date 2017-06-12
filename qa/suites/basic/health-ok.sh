#!/bin/bash -ex
#
# DeepSea integration test "suites/basic/health-ok.sh"
#
# This script runs DeepSea stages 0-3 to deploy a Ceph cluster on all the nodes
# that have at least one external disk drive. After stage 3 completes, the
# script checks for HEALTH_OK.
#
# The script makes no assumptions beyond those listed in qa/README.
#
# On success (HEALTH_OK is reached), the script returns 0. On failure, for
# whatever reason, the script returns non-zero.
#
# The script produces verbose output on stdout, which can be captured for later
# forensic analysis.
#
# FIXME:
# - script currently tolerates HEALTH_WARN -> not good. The only HEALTH_WARN
#   outcome it should tolerate is clock skew. (We will need a special ceph.conf
#   for two-node clusters.)

BASEDIR=$(pwd)
source $BASEDIR/common/common.sh

run_stage_0
run_stage_1
gen_policy_cfg_base
gen_policy_cfg_no_client
cat_policy_cfg
run_stage_2
run_stage_3
ceph_health_test

echo "OK"
