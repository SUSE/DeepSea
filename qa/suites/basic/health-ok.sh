#!/bin/bash
#
# DeepSea integration test "suites/basic/health-ok.sh"
#
# This script runs DeepSea stages 0-3 to deploy a Ceph cluster, optionally
# with data-at-rest encryption of OSDs, on all the nodes that have at least
# one external disk drive. After stage 3 completes, the script checks for
# HEALTH_OK and tests the "ceph.restart" orchestration if --mini is not provided.
#
# The script makes no assumptions beyond those listed in qa/README.
#
# On success (HEALTH_OK is reached and optionally "ceph.restart" orchestration behaves
# as expected), the script returns 0. On failure, for whatever reason, the
# script returns non-zero.
#
# The script produces verbose output on stdout, which can be captured for later
# forensic analysis.
#

set -ex

SCRIPTNAME=$(basename ${0})
BASEDIR=$(readlink -f "$(dirname ${0})/../..")
test -d $BASEDIR
[[ $BASEDIR =~ \/qa$ ]]

source $BASEDIR/common/common.sh $BASEDIR

function usage {
    set +x
    echo "$SCRIPTNAME - script for testing HEALTH_OK deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  $SCRIPTNAME [-h,--help] [--cli] [--mini]"
    echo
    echo "Options:"
    echo "    --cli         Use DeepSea CLI"
    echo "    --encryption  Deploy OSDs with data-at-rest encryption"
    echo "    --mini        Omit long-running tests"
    echo "    --help        Display this usage message"
    exit 1
}

assert_enhanced_getopt

TEMP=$(getopt -o h --long "cli,encrypted,encryption,help,mini,smoke" \
     -n 'health-ok.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process command-line options
CLI=""
ENCRYPTION=""
MINI=""
while true ; do
    case "$1" in
        --cli) CLI="$1" ; shift ;;
        --encrypted|--encryption) ENCRYPTION="$1" ; shift ;;
        --mini|--smoke) MINI="$1" ; shift ;;
        -h|--help) usage ;;    # does not return
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done

# deploy phase
MIN_NODES=1
CLIENT_NODES=0
deploy_ceph

# test phase
ceph_health_test
ceph_log_grep_enoent_eaccess
test_systemd_ceph_osd_target_wants
rados_write_test
ceph_version_test
if [ -z "$MINI" ] ; then
    run_stage_0 "$CLI"
    restart_services
    mon_restarted "1" # 1 means not restarted
    osd_restarted "1"
    # apply config change
    change_osd_conf
    change_mon_conf
    # construct and spread config
    run_stage_3 "$CLI"
    restart_services
    mon_restarted "0" # 0 means restarted
    osd_restarted "0"
    # make sure still in HEALTH_OK
    ceph_cluster_status
    ceph_health_test
fi

echo "health-ok test result: PASS"
