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

function usage {
    set +x
    echo "${0} - script for testing iSCSI Gateway (igw) deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  ${0} [-h,--help] [--cli]"
    echo
    echo "Options:"
    echo "    --cli      Use DeepSea CLI"
    echo "    --help     Display this usage message"
    exit 1
}

TEMP=$(getopt -o h --long "cli" \
     -n 'health-igw.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
CLI=""
while true ; do
    case "$1" in
        --cli) CLI="cli" ; shift ;;
        -h|--help) usage ;;    # does not return
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done

assert_enhanced_getopt
install_deps
cat_salt_config
run_stage_0 "$CLI"
run_stage_1 "$CLI"
policy_cfg_base
policy_cfg_mon_flex
policy_cfg_igw
policy_cfg_storage 1 # last node will be "client" (not storage)
cat_policy_cfg
run_stage_2 "$CLI"
ceph_conf_small_cluster
run_stage_3 "$CLI"
ceph_cluster_status
run_stage_4 "$CLI"
ceph_cluster_status
ceph_health_test
iscsi_kludge # see bsc#1049669
igw_info
iscsi_mount_and_sanity_test
run_stage_0 "$CLI"

echo "OK"
