#!/bin/bash
#
# DeepSea integration test "suites/basic/health-ok.sh"
#
# This script runs DeepSea stages 0-3 (or 0-4, depending on options) to deploy
# a Ceph cluster, optionally with RGW, MDS, and/or data-at-rest encryption of
# OSDs, on all the nodes that have at least one external disk drive. After the
# last stage completes, the script checks for HEALTH_OK.
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

SCRIPTNAME=$(basename ${0})
BASEDIR=$(readlink -f "$(dirname ${0})/../..")
test -d $BASEDIR
[[ $BASEDIR =~ \/qa$ ]]

source $BASEDIR/common/common.sh

function usage {
    set +x
    echo "$SCRIPTNAME - script for testing HEALTH_OK deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  $SCRIPTNAME [-h,--help] [--cli] [--client-nodes=X]"
    echo "  [--encryption] [--mds] [--min-nodes=X] [--rgw] [--ssl]"
    echo
    echo "Options:"
    echo "    --cli           Use DeepSea CLI"
    echo "    --client-nodes  Number of client (non-cluster) nodes"
    echo "    --encryption    Deploy OSDs with data-at-rest encryption"
    echo "    --mds           Deploy MDS"
    echo "    --min-nodes     Minimum number of nodes"
    echo "    --help          Display this usage message"
    echo "    --rgw           Deploy RGW"
    echo "    --ssl           Deploy RGW with SSL"
    exit 1
}

assert_enhanced_getopt

TEMP=$(getopt -o h \
--long "cli,client-nodes:,encrypted,encryption,help,mds,min-nodes:,rgw,ssl" \
-n 'health-ok.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process command-line options
CLI=""
CLIENT_NODES=0
STORAGE_PROFILE="default"
MDS=""
MIN_NODES=1
RGW=""
SSL=""
while true ; do
    case "$1" in
        --cli) CLI="$1" ; shift ;;
        --client-nodes) shift ; CLIENT_NODES=$1 ; shift ;;
        --encrypted|--encryption) STORAGE_PROFILE="dmcrypt" ; shift ;;
        --mds) MDS="$1" ; shift ;;
        --min-nodes) shift ; MIN_NODES=$1 ; shift ;;
        -h|--help) usage ;;    # does not return
        --rgw) RGW="$1" ; shift ;;
        --ssl) SSL="$1" ; shift ;;
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done
echo "WWWW"
echo "Running health-ok.sh with options $CLI $ENCRYPTION $MDS $RGW $SSL"

# deploy phase
deploy_ceph

# test phase
ceph_health_test
ceph_log_grep_enoent_eaccess
test_systemd_ceph_osd_target_wants
rados_write_test
ceph_version_test
if [ -n "$RGW" ] ; then
    rgw_curl_test
    test -n "$SSL" && validate_rgw_cert_perm
    rgw_user_and_bucket_list
    rgw_validate_system_user
fi
test -n "$MDS" -a "$CLIENT_NODES" -ge 1 && cephfs_mount_and_sanity_test

echo "YYYY"
echo "health-ok test result: PASS"
