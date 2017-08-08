#!/bin/bash -ex
#
# DeepSea integration test "suites/ceph-test/pynfs.sh"
#
# This script runs DeepSea stages 0-4 to deploy a Ceph cluster with MDS and
# NFS-Ganesha.  After stage 4 completes, it runs the PyNFS test suite.
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

BASEDIR=$(pwd)
source $BASEDIR/common/common.sh
source $BASEDIR/common/nfs-ganesha.sh

function usage {
    set +x
    echo "${0} - script for testing NFS Ganesha deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  ${0} [--fsal={cephfs,rgw,both}]"
    echo
    echo "Options:"
    echo "    --fsal     Defaults to cephfs"
    exit 1
}

TEMP=$(getopt -o h --long "fsal:" \
     -n 'health-nfs-ganesha.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
FSAL=cephfs
while true ; do
    case "$1" in
        -h|--help) usage ;;    # does not return
        --fsal) FSAL=$2 ; shift ; shift ;;
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
run_stage_0
run_stage_1
policy_cfg_base
policy_cfg_client
if [ "$FSAL" = "cephfs" -o "$FSAL" = "both" ] ; then
    policy_cfg_mds
fi
if [ "$FSAL" = "rgw" -o "$FSAL" = "both" ] ; then
    policy_cfg_rgw
    rgw_demo_users
fi
policy_cfg_nfs_ganesha
cat_policy_cfg
run_stage_2
ceph_conf_small_cluster
run_stage_3
ceph_cluster_status
nfs_ganesha_no_root_squash
run_stage_4
ceph_cluster_status
ceph_health_test
nfs_ganesha_cat_config_file
nfs_ganesha_debug_log
nfs_ganesha_showmount_loop
if [ "$FSAL" = "cephfs" ] ; then
    nfs_ganesha_pynfs_test
else
    echo "This test supports CephFS FSAL only. Bailing out."
    exit 1
fi

echo "OK"
