#!/bin/bash
#
# DeepSea integration test "suites/basic/health-openattic.sh"
#
# This script runs DeepSea stages 0-4 to deploy a Ceph cluster with RADOS Gateway,
# iSCSI Gateway, NFS-Ganesha, and openATTIC. After stage 4 completes, it should
# use openATTIC REST API calls to validate functionality, but this is still a 
# FIXME/TODO item.
#
# This script makes the following assumption beyond those listed in qa/README:
# - minimum of 3 nodes in cluster
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
source $BASEDIR/common/nfs-ganesha.sh

function usage {
    set +x
    echo "${0} - script for testing openATTIC deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  ${0} [-h,--help] [--apparmor] [--cli]"
    echo
    echo "Options:"
    echo "    --apparmor Use AppArmor"
    echo "    --cli      Use DeepSea CLI"
    echo "    --help     Display this usage message"
    exit 1
}

TEMP=$(getopt -o h --long "apparmor,cli,help" \
     -n 'health-openattic.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
APPARMOR=""
CLI=""
while true ; do
    case "$1" in
        --apparmor) APPARMOR="$1" ; shift ;;
        --cli) CLI="cli" ; shift ;;
        -h|--help) usage ;;    # does not return
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done

assert_enhanced_getopt
install_deps
cat_salt_config
test -n "$APPARMOR" && ceph_apparmor
run_stage_0 "$CLI"
salt_api_test
run_stage_1 "$CLI"
policy_cfg_base
policy_cfg_mon_flex
policy_cfg_mds
policy_cfg_openattic_rgw_igw_nfs
policy_cfg_storage 0 # "0" means all nodes will have storage role
cat_policy_cfg
rgw_demo_users
run_stage_2 "$CLI"
ceph_conf_small_cluster
run_stage_3 "$CLI"
ceph_cluster_status
create_all_pools_at_once iscsi-images cephfs_data cephfs_metadata
nfs_ganesha_no_root_squash
run_stage_4 "$CLI"
ceph_cluster_status
ceph_health_test
nfs_ganesha_cat_config_file
nfs_ganesha_debug_log
rgw_curl_test
rgw_user_and_bucket_list
ceph_version_test
run_stage_0 "$CLI"

echo "OK"
