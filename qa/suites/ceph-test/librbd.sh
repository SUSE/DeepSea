#!/bin/bash
#
# DeepSea integration test "suites/ceph-test/librbd.sh"
#
# This script deploys a basic cluster and tests that ceph_test_librbd can be
# run on the client node. That means it's probably only useful if you execute
# that command yourself (manually or via CI tooling) after this script runs.
#
# The script makes the following assumption beyond those listed in qa/README:
# - the ceph-test RPM is installed on the client node
#
# On success (script thinks ceph_test_librbd can be run), the script returns 0.
# On failure, for whatever reason, the script returns non-zero.
#
# The script produces verbose output on stdout, which can be captured for later
# forensic analysis.
#

set -ex
BASEDIR=$(pwd)
source $BASEDIR/common/common.sh

function usage {
    set +x
    echo "${0} - script for testing RBD (CLI and librbd)"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  ${0} [-h,--help] [--apparmor] [--cli]"
    echo
    echo "Options:"
    echo "    --apparmor    Use AppArmor"
    echo "    --cli         Use DeepSea CLI"
    echo "    --help        Display this usage message"
    exit 1
}

TEMP=$(getopt -o h --long "apparmor,cli,help" \
     -n "$0" -- "$@")

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

install_deps
cat_salt_config
test -n "$APPARMOR" && ceph_apparmor
run_stage_0 "$CLI"
run_stage_1 "$CLI"
policy_cfg_base
policy_cfg_mon_flex
policy_cfg_storage 1 # one node will be a "client" (no storage role)
cat_policy_cfg
run_stage_2 "$CLI"
ceph_conf_small_cluster
ceph_conf_mon_allow_pool_delete
ceph_conf_upstream_rbd_default_features
run_stage_3 "$CLI"
ceph_cluster_status
ceph_health_test
ceph_test_librbd_can_be_run

echo "OK, now you can exercise RBD (CLI and librbd)"
