#!/bin/bash
#
# DeepSea integration test "suites/basic/health-all.sh"
#
# This script runs DeepSea stages 0-4 to deploy a Ceph cluster with all roles.
# After stage 4 completes, a number of sanity checks are run to verify that
# the roles are functional.
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

SCRIPTNAME=$(basename ${0})
BASEDIR=$(readlink -f "$(dirname ${0})/../..")
test -d $BASEDIR
[[ $BASEDIR =~ \/qa$ ]]

source $BASEDIR/common/common.sh $BASEDIR

function usage {
    set +x
    echo "$SCRIPTNAME - script for testing DeepSea deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  $SCRIPTNAME [-h,--help] [--cli] [--encrypted] [--mini] [--ssl]"
    echo
    echo "Options:"
    echo "    --cli        Use DeepSea CLI"
    echo "    --encrypted  Deploy OSDs with data-at-rest encryption"
    echo "    --help       Display this usage message"
    echo "    --mini       Omit restart orchestration test"
    echo "    --ssl        Use SSL (https, port 443) with RGW"
    exit 1
}

set +x

TEMP=$(getopt -o h --long "cli,encrypted,encryption,help,mini,ssl" \
     -n 'health-all.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
CLI=""
ENCRYPTION=""
MINI=""
SSL=""
while true ; do
    case "$1" in
        --cli) CLI="$1" ; shift ;;
        --encrypted|--encryption) ENCRYPTION="$1" ; shift ;;
        -h|--help) usage ;;    # does not return
        --mini) MINI="$1" ; shift ;;
        --ssl) SSL="$1" ; shift ;;
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done
echo "WWWW"
echo "Running health-all.sh with options $CLI $ENCRYPTION $MINI $SSL"

set -x

$BASEDIR/suites/basic/health-stages.sh "$CLI" "$ENCRYPTION" "--cephfs" "--nfs-ganesha" "--rgw" "$SSL"

$BASEDIR/common/sanity-basic.sh $BASEDIR
$BASEDIR/common/sanity-cephfs.sh $BASEDIR

# additional sanity checks
nfs_ganesha_cat_config_file
nfs_ganesha_debug_log
rgw_curl_test
if [ -n "$SSL" ] ; then
    rgw_curl_test_ssl
    validate_rgw_cert_perm
fi
rgw_user_and_bucket_list
echo "WWWW"
echo "additional sanity checks OK"

if [ -z "$MINI" ] ; then
    run_stage_0 "$CLI"
    echo "WWWW"
    echo "re-run of Stage 0 OK"
fi
