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
BASEDIR=$(pwd)
source $BASEDIR/common/common.sh

function usage {
    set +x
    echo "${0} - script for testing HEALTH_OK deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  ${0} [-h,--help] [--cli]"
    echo
    echo "Options:"
    echo "    --cli         Use DeepSea CLI"
    echo "    --encryption  Deploy OSDs with data-at-rest encryption"
    echo "    --mini        Only uses a bare minimum of tests"
    echo "    --help        Display this usage message"
    exit 1
}

TEMP=$(getopt -o h --long "cli,encrypted,encryption,help" \
     -n 'health-ok.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
CLI=""
ENCRYPTION=""
MINI=""
while true ; do
    case "$1" in
        --cli) CLI="cli" ; shift ;;
        --encrypted|--encryption) ENCRYPTION="encryption" ; shift ;;
        --mini|--smoke) MINI="mini" ; shift ;;
        -h|--help) usage ;;    # does not return
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done

assert_enhanced_getopt
install_deps
cat_salt_config
run_stage_0 "$CLI"
salt_api_test
run_stage_1 "$CLI"
if [ -n "$ENCRYPTION" ] ; then
    proposal_populate_dmcrypt
fi
policy_cfg_base
policy_cfg_mon_flex
policy_cfg_storage 0 $ENCRYPTION # "0" means all nodes will have storage role
cat_policy_cfg
run_stage_2 "$CLI"
ceph_conf_small_cluster
run_stage_3 "$CLI"
ceph_cluster_status
ceph_health_test
ceph_log_grep_enoent_eaccess
test_systemd_ceph_osd_target_wants
create_all_pools_at_once write_test
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

echo "OK"
