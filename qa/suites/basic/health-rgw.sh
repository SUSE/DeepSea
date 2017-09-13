#!/bin/bash
#
# DeepSea integration test "suites/basic/health-rgw.sh"
#
# This script runs DeepSea stages 0-4 to deploy a Ceph cluster with RGW.  After
# stage 4 completes, it sends a GET request to the RGW node using curl, and
# tests that: (a) the response contains the string "anonymous" and (b) the
# response is legal XML.
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
    echo "${0} - script for testing RADOS Gateway deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  ${0} [-h,--help] [--cli] [--ssl]"
    echo
    echo "Options:"
    echo "    --cli      Use DeepSea CLI"
    echo "    --help     Display this usage message"
    echo "    --ssl      Use SSL (https, port 443) with RGW"
    exit 1
}

TEMP=$(getopt -o h --long "cli,ssl" \
     -n 'health-rgw.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
CLI=""
SSL=""
while true ; do
    case "$1" in
        --cli) CLI="cli" ; shift ;;
        -h|--help) usage ;;    # does not return
        --ssl) SSL="ssl" ; shift ;;
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done

assert_enhanced_getopt
install_deps
cat_salt_config
run_stage_0 "$CLI"
if [ -n "$SSL" ] ; then
    echo "Testing RGW deployment with SSL"
    rgw_ssl_init
else
    echo "Testing RGW deployment (no SSL)"
fi
run_stage_1 "$CLI"
policy_cfg_base
policy_cfg_no_client
if [ -n "$SSL" ] ; then
    policy_cfg_rgw_ssl
else
    policy_cfg_rgw
fi
cat_policy_cfg
run_stage_2 "$CLI"
ceph_conf_small_cluster
run_stage_3 "$CLI"
ceph_cluster_status
run_stage_4 "$CLI"
ceph_cluster_status
rgw_user_and_bucket_list
ceph_health_test
rgw_curl_test
if [ -n "$SSL" ] ; then
    rgw_curl_test_ssl
fi

echo "OK"
