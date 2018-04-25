#!/bin/bash
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

set -ex

SCRIPTNAME=$(basename ${0})
BASEDIR=$(readlink -f "$(dirname ${0})/../..")
test -d $BASEDIR
[[ $BASEDIR =~ \/qa$ ]]

source $BASEDIR/common/common.sh

function usage {
    set +x
    echo "$SCRIPTNAME - script for testing CephFS deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  $SCRIPTNAME [-h,--help] [--cli] [--mini]"
    echo
    echo "Options:"
    echo "    --cli      Use DeepSea CLI"
    echo "    --help     Display this usage message"
    echo "    --mini     Omit long-running tests"
    exit 1
}

TEMP=$(getopt -o h --long "cli,help,mini,smoke" \
     -n 'health-mds.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
CLI=""
MINI=""
while true ; do
    case "$1" in
        --cli) CLI="$1" ; shift ;;
        -h|--help) usage ;;    # does not return
        --mini|--smoke) MINI="$1" ; shift ;;
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done

# deploy phase
MIN_NODES=2
CLIENT_NODES=1
MDS="--mds"
deploy_ceph

# test phase
ceph_health_test
cephfs_mount_and_sanity_test
if [ -z "$MINI" ] ; then
    run_stage_0 "$CLI"
fi

echo "OK"
