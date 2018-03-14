#!/bin/bash -ex
#
# DeepSea integration test "suites/basic/health-nfs-ganesha.sh"
#
# This script runs DeepSea stages 0-4 to deploy a Ceph cluster with MDS and
# NFS-Ganesha.  After stage 4 completes, it mounts the NFS-Ganesha on the
# client node, touches a file, and asserts that it exists.
#
# The script makes no assumptions beyond those listed in qa/README.
#
# This script takes an optional command-line option, "--fsal", which can
# be either "cephfs", "rgw", or "both". If the option is absent, the value
# defaults to "cephfs".
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
source $BASEDIR/common/nfs-ganesha.sh

function usage {
    set +x
    echo "$SCRIPTNAME - script for testing NFS-Ganesha deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  $SCRIPTNAME [-h,--help] [--cli] [--fsal={cephfs,rgw,both}]"
    echo
    echo "Options:"
    echo "    --cli      Use DeepSea CLI"
    echo "    --fsal     Defaults to cephfs"
    echo "    --help     Display this usage message"
    exit 1
}

TEMP=$(getopt -o h --long "cli,fsal:,help" \
     -n 'health-nfs-ganesha.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
CLI=""
FSAL=cephfs
while true ; do
    case "$1" in
        --cli) CLI="cli" ; shift ;;
        --fsal) FSAL=$2 ; shift ; shift ;;
        -h|--help) usage ;;    # does not return
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done

case "$FSAL" in
    cephfs) break ;;
    rgw) break ;;
    both) break ;;
    *) usage ;; # does not return
esac

echo "Testing deployment with FSAL ->$FSAL<-"

assert_enhanced_getopt
install_deps
cat_salt_config
run_stage_0 "$CLI"
salt_api_test
run_stage_1 "$CLI"
policy_cfg_base
policy_cfg_mon_flex
if [ "$FSAL" = "cephfs" -o "$FSAL" = "both" ] ; then
    policy_cfg_mds
fi
if [ "$FSAL" = "rgw" -o "$FSAL" = "both" ] ; then
    policy_cfg_rgw
    rgw_demo_users
fi
policy_cfg_nfs_ganesha
policy_cfg_storage 1 # last node will be "client" (not storage)
cat_policy_cfg
run_stage_2 "$CLI"
ceph_conf_small_cluster
run_stage_3 "$CLI"
ceph_cluster_status
if [ "$FSAL" = "cephfs" -o "$FSAL" = "both" ] ; then
  create_all_pools_at_once cephfs_data cephfs_metadata
fi
nfs_ganesha_no_root_squash
run_stage_4 "$CLI"
ceph_cluster_status
ceph_health_test
nfs_ganesha_cat_config_file
nfs_ganesha_debug_log
# kludge to work around mount hang
#nfs_ganesha_showmount_loop
for v in "" "3" "4" ; do
    echo "Testing NFS-Ganesha with NFS version ->$v<-"
    if [ "$FSAL" = "rgw" -a "$v" = "3" ] ; then
        echo "Not testing RGW FSAL on NFSv3"
        continue
    else
        nfs_ganesha_mount "$v"
    fi
    if [ "$FSAL" = "cephfs" -o "$FSAL" = "both" ] ; then
        nfs_ganesha_write_test cephfs "$v"
    fi
    if [ "$FSAL" = "rgw" -o "$FSAL" = "both" ] ; then
        if [ "$v" = "3" ] ; then
            echo "Not testing RGW FSAL on NFSv3"
        else
            rgw_curl_test
            rgw_user_and_bucket_list
            rgw_validate_demo_users
            nfs_ganesha_write_test rgw "$v"
        fi
    fi
    nfs_ganesha_umount
    sleep 10
done
run_stage_0 "$CLI"

echo "OK"
