#!/bin/bash
#
# DeepSea integration test "suites/basic/health-rgw.sh"
#
# This script runs DeepSea stages 0-4 to deploy a Ceph cluster with RGW (and
# optionally RGW+SSL). After stage 4 completes, it sends a GET request to the
# RGW node using curl (optionally using SSL endpoint), and tests that: (a) the
# response contains the string "anonymous" and (b) the response is legal XML.
# The script also deploys some RGW demo users.
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
    echo "$SCRIPTNAME - script for testing RADOS Gateway deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  $SCRIPTNAME [-h,--help] [--cli] [--mini] [--ssl]"
    echo
    echo "Options:"
    echo "    --cli      Use DeepSea CLI"
    echo "    --help     Display this usage message"
    echo "    --mini     Omit long-running tests"
    echo "    --ssl      Use SSL (https, port 443) with RGW"
    exit 1
}

TEMP=$(getopt -o h --long "cli,help,mini,smoke,ssl" \
     -n 'health-rgw.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process command-line options
CLI=""
MINI=""
SSL=""
while true ; do
    case "$1" in
        --cli) CLI="$1" ; shift ;;
        -h|--help) usage ;;    # does not return
        --mini|--smoke) MINI="$1" ; shift ;;
        --ssl) SSL="$1" ; shift ;;
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done

# deploy phase
MIN_NODES=1
CLIENT_NODES=0
STORAGE_PROFILE="default"
RGW="--rgw"
deploy_ceph

# test phase
ceph_health_test
rgw_curl_test
test -n "$SSL" && validate_rgw_cert_perm
rgw_user_and_bucket_list
rgw_validate_system_user
ceph_health_test
if [ -z "$MINI" ] ; then
    run_stage_0 "$CLI"
    restart_services
    rgw_restarted "1" # 1 means not restarted
    # apply config change
    change_rgw_conf
    # construct and spread config
    run_stage_3 "$CLI"
    restart_services
    rgw_restarted "0" # 0 means restarted
fi

echo "health-rgw test result: PASS"
