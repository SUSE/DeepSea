#!/bin/bash -ex
#
# DeepSea integration test "suites/basic/health-nfs-ganesha.sh"
#
# This script runs DeepSea stages 0-4 to deploy a Ceph cluster with MDS and
# NFS-Ganesha.  After stage 4 completes, it mounts the NFS-Ganesha on the
# client node and runs some basic tests according to the --fsal setting (see
# below).
#
# The script makes no assumptions beyond those listed in qa/README.
#
# This script takes an optional command-line option, "--fsal", which can be
# either "cephfs", "rgw", or "both". If the option is absent, the value
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

source $BASEDIR/common/common.sh

function usage {
    set +x
    echo "$SCRIPTNAME - script for testing NFS-Ganesha deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  $SCRIPTNAME [-h,--help] [--cli] [--fsal={cephfs,rgw,both}]"
    echo "              [--mini]"
    echo
    echo "Options:"
    echo "    --cli      Use DeepSea CLI"
    echo "    --fsal     Defaults to cephfs"
    echo "    --help     Display this usage message"
    echo "    --mini     Omit long-running tests"
    exit 1
}

TEMP=$(getopt -o h --long "cli,fsal:,help,mini,smoke" \
     -n 'health-nfs-ganesha.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
CLI=""
FSAL="cephfs"
MINI=""
while true ; do
    case "$1" in
        --cli) CLI="cli" ; shift ;;
        --fsal) FSAL=$2 ; shift ; shift ;;
        -h|--help) usage ;;    # does not return
        --mini|--smoke) MINI="$1" ; shift ;;
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done

MDS=""
RGW=""
case "$FSAL" in
    cephfs) MDS="--mds" ; break ;;
    rgw) RGW="--rgw" ; break ;;
    both) MDS="--mds" ; RGW="--rgw" ; break ;;
    *) usage ;; # does not return
esac

# deploy phase
echo "Deploying NFS-Ganesha with FSAL ->$FSAL<-"
MIN_NODES=2
CLIENT_NODES=1
NFS_GANESHA="--nfs-ganesha"
deploy_ceph

# test phase
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

if [ -z "$MINI" ] ; then
    run_stage_0 "$CLI"
fi

echo "OK"
