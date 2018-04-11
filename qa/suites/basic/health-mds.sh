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

source $BASEDIR/common/common.sh $BASEDIR

function usage {
    set +x
    echo "$SCRIPTNAME - script for testing CephFS deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  $SCRIPTNAME [-h,--help] [--cli] [--encrypted] [--mini]"
    echo
    echo "Options:"
    echo "    --cli        Use DeepSea CLI"
    echo "    --encrypted  Deploy OSDs with data-at-rest encryption"
    echo "    --help       Display this usage message"
    echo "    --mini       Omit restart orchestration test"
    exit 1
}

set +x

TEMP=$(getopt -o h --long "cli,encrypted,encryption,help,mini" \
     -n 'health-mds.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
CLI=""
ENCRYPTION=""
MINI=""
while true ; do
    case "$1" in
        --cli) CLI="$1" ; shift ;;
        --encrypted|--encryption) ENCRYPTION="$1" ; shift ;;
        -h|--help) usage ;;    # does not return
        --mini) MINI="$1" ; shift ;;
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done
echo "WWWW"
echo "Running health-mds.sh with options $CLI $ENCRYPTION $MINI"

set -x

$BASEDIR/suites/basic/health-stages.sh "--cephfs" "$CLI" "--client-nodes=1" "$ENCRYPTION" "--min-nodes=2"

$BASEDIR/common/sanity-basic.sh $BASEDIR
$BASEDIR/common/sanity-cephfs.sh $BASEDIR

if [ -z "$MINI" ] ; then
    run_stage_0 "$CLI"
    echo "WWWW"
    echo "restart orchestration OK"
fi
