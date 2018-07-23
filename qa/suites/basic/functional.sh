#!/bin/bash
#
# DeepSea integration test "suites/basic/functional.sh"
#
# This script runs DeepSea stages 0-3 to deploy a Ceph cluster on all available
# nodes (each node should have 4 external disk drives). After stage 3
# completes, the script checks for HEALTH_OK and triggers the "ceph.smoketests"
# orchestration.
#
# In addition to the assumptions listed in qa/README, this script assumes that
# all test nodes will have four external disk drives (i.e. in addition to the 
# drive containing the root filesystem).
#
# On success (HEALTH_OK is reached and "ceph.smoketests" orchestration behaves
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

source $BASEDIR/common/common.sh

function usage {
    set +x
    echo "$SCRIPTNAME - script for testing HEALTH_OK deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  $SCRIPTNAME [-h,--help]"
    echo
    echo "Options:"
    echo "    --cli         Use DeepSea CLI"
    echo "    --help        Display this usage message"
    exit 1
}

assert_enhanced_getopt

TEMP=$(getopt -o h \
--long "cli,help" \
-n 'functional.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process command-line options
CLI=""
while true ; do
    case "$1" in
        --cli) CLI="$1" ; shift ;;
        -h|--help) usage ;;    # does not return
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done
echo "WWWW"
echo "Running $SCRIPTNAME with options $CLI"

# deploy phase
MIN_NODES=1
CLIENT_NODES=0
deploy_ceph

# test phase
ceph_health_test
run_orchestration 'ceph.smoketests'

echo "$SCRIPTNAME result: PASS"
