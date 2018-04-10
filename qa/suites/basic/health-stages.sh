#!/bin/bash
#
# DeepSea integration test "suites/basic/health-stages.sh"
#
# This script runs DeepSea stages to deploy a Ceph cluster. Various roles
# and configurations can be set using command-line options. No testing is done,
# other than to check for HEALTH_OK.
#
# This script makes no assumption beyond those listed in qa/README.
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
    echo "  $SCRIPTNAME [-h,--help] [--cephfs] [--cli] [--client-nodes=X]"
    echo "              [--dashboard] [--encrypted] [--min-nodes=X] [--nfs-ganesha]"
    echo "              [--no-reboot] [--rgw] [--ssl]"
    echo
    echo "Options:"
    echo "    --help           Display this usage message"
    echo "    --cephfs         Deploy CephFS"
    echo "    --cli            Use DeepSea CLI"
    echo "    --client-nodes=X Number of client nodes (default: 0)"
    echo "    --dashboard      Deploy with dashboard MGR module"
    echo "    --encrypted      Deploy OSDs with data-at-rest encryption"
    echo "    --min-nodes=X    Minimum number of nodes (default: 1)"
    echo "    --nfs-ganesha    Deploy NFS-Ganesha"
    echo "    --no-reboot      Disable Stage 0 reboot"
    echo "    --rgw            Deploy RGW"
    echo "    --ssl            Use SSL (https, port 443) with RGW"
    exit 1
}

set +x

TEMP=$(getopt -o h \
     --long "cephfs,cli,client-nodes:,dashboard,encrypted,encryption,help,min-nodes:,nfs-ganesha,no-reboot,rgw,ssl" \
     -n 'health-stages.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
CEPHFS=""
CLI=""
CLIENT_NODES="0"
DASHBOARD=""
ENCRYPTION=""
PROPOSED_MIN_NODES=""
NFS_GANESHA=""
RGW=""
NO_REBOOT=""
SSL=""
while true ; do
    case "$1" in
        --cephfs) CEPHFS="$1" ; shift ;;
        --cli) CLI="$1" ; shift ;;
        --client-nodes) CLIENT_NODES="$2" ; shift ; shift ;;
        --dashboard) DASHBOARD="$1" ; shift ;;
        --encrypted|--encryption) ENCRYPTION="$1" ; shift ;;
        --min-nodes) PROPOSED_MIN_NODES="$2" shift ; shift ;;
        --nfs-ganesha) NFS_GANESHA="$1" ; shift ;;
        --no-reboot) NO_REBOOT="$1" ; shift ;;
        -h|--help) usage ;;    # does not return
        --rgw) RGW="$1" ; shift ;;
        --ssl) SSL="$1" ; shift ;;
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done
MIN_NODES=$(($CLIENT_NODES + 1))
if [ -n "$PROPOSED_MIN_NODES" ] ; then
    if [ "$PROPOSED_MIN_NODES" -lt "$MIN_NODES" ] ; then
        echo "--min-nodes value is too low. Need at least 1 + --client-nodes"
        exit 1
    fi
    test "$PROPOSED_MIN_NODES" -gt "$MIN_NODES" && MIN_NODES="$PROPOSED_MIN_NODES"
fi

set -x

assert_enhanced_getopt
install_deps
global_test_setup

echo "WWWW"
echo -n "Running health-stages.sh with options "
echo "$CEPHFS $CLI --client-nodes=$CLIENT_NODES $DASHBOARD $ENCRYPTION --min-nodes=$MIN_NODES $NFS_GANESHA $RGW $SSL"
TOTAL_NODES=$(json_total_nodes)
test "$TOTAL_NODES" -ge "$MIN_NODES"
CLUSTER_NODES=$(($TOTAL_NODES - $CLIENT_NODES))
echo "WWWW"
echo "This script will use DeepSea to deploy a cluster of $TOTAL_NODES nodes total (including Salt Master)."
echo "Of these, $CLIENT_NODES will be clients (nodes without any DeepSea roles except \"admin\")."

cat_salt_config
test -n "$NO_REBOOT" && disable_restart_in_stage_0
run_stage_0 "$CLI"
test -n "$RGW" -a -n "$SSL" && rgw_ssl_init || true
salt_api_test
run_stage_1 "$CLI"
test -n "$ENCRYPTION" && proposal_populate_dmcrypt
policy_cfg_base
policy_cfg_mon_flex "$CLUSTER_NODES"
test -n "$CEPHFS" && policy_cfg_mds "$CLUSTER_NODES"
test -n "$RGW" && policy_cfg_rgw "$CLUSTER_NODES" "$SSL"
test -n "$NFS_GANESHA" && policy_cfg_nfs_ganesha "$CLUSTER_NODES"
test -n "$NFS_GANESHA" -a -n "$RGW" && rgw_demo_users
policy_cfg_storage "$CLIENT_NODES" "$ENCRYPTION"
cat_policy_cfg
rgw_demo_users
run_stage_2 "$CLI"
ceph_conf_adjustments "$DASHBOARD"
run_stage_3 "$CLI"

# pre-create pools with calculated number of PGs so we don't get health
# warnings after Stage 4 due to "too few" or "too many" PGs per OSD
# (the "write_test" pool is used in common/sanity-basic.sh)
sleep 10
if [ -n "$CEPHFS" ] ; then
    create_all_pools_at_once write_test cephfs_data cephfs_metadata
else
    create_all_pools_at_once write_test
fi
ceph osd pool application enable write_test deepsea_qa
sleep 10
ceph_cluster_status
ceph_health_test

if [ -z "$CEPHFS" -a -z "$NFS_GANESHA" -a -z "$RGW" ] ; then
    echo "WWWW"
    echo "Stages 0-3 OK"
    echo "No roles requiring Stage 4: stopping here"
    exit 0
fi

test -n "$NFS_GANESHA" && nfs_ganesha_no_root_squash
run_stage_4 "$CLI"
ceph_cluster_status
ceph_health_test

echo "WWWW"
echo "Stage 4 OK"

if [ -n "$NFS_GANESHA" ] ; then
    nfs_ganesha_cat_config_file
    nfs_ganesha_debug_log
    echo "WWWW"
    echo "NFS-Ganesha set to debug logging"
fi
