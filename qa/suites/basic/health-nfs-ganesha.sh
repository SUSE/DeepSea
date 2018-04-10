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

function usage {
    set +x
    echo "$SCRIPTNAME - script for testing NFS-Ganesha deployment"
    echo "for use in SUSE Enterprise Storage testing"
    echo
    echo "Usage:"
    echo "  $SCRIPTNAME [-h,--help] [--cli] [--encryption]"
    echo "              [--fsal={cephfs,rgw,both}] [--mini]"
    echo
    echo "Options:"
    echo "    --cli         Use DeepSea CLI"
    echo "    --encryption  Deploy OSDs with data-at-rest encryption"
    echo "    --fsal        Defaults to cephfs"
    echo "    --help        Display this usage message"
    echo "    --mini        Omit restart orchestration test"
    exit 1
}

set +x

TEMP=$(getopt -o h --long "cli,encrypted,encryption,fsal:,help,mini" \
     -n 'health-nfs-ganesha.sh' -- "$@")

if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi

# Note the quotes around TEMP': they are essential!
eval set -- "$TEMP"

# process options
CLI=""
ENCRYPTION=""
FSAL=cephfs
MINI=""
while true ; do
    case "$1" in
        --cli) CLI="$1" ; shift ;;
        --encrypted|--encryption) ENCRYPTION="$1" ; shift ;;
        --fsal) FSAL=$2 ; shift ; shift ;;
        --mini|--smoke) MINI="$1" ; shift ;;
        -h|--help) usage ;;    # does not return
        --) shift ; break ;;
        *) echo "Internal error" ; exit 1 ;;
    esac
done
echo "WWWW"
echo "Running health-nfs-ganesha.sh with options $CLI $ENCRYPTION --fsal=$FSAL $MINI"

CEPHFS=""
KEY_OPTS=""
RGW=""
case "$FSAL" in
    cephfs) 
        CEPHFS="--cephfs"
        KEY_OPTS="--nfs-ganesha --cephfs"
        ;;
    rgw)
        RGW="--rgw"
        KEY_OPTS="--nfs-ganesha --rgw $SSL"
        ;;
    both)
        CEPHFS="--cephfs"
        RGW="--rgw"
        KEY_OPTS="--nfs-ganesha --cephfs --rgw $SSL"
        ;;
    *)
        usage # does not return
        ;;
esac

set -x

$BASEDIR/suites/basic/health-stages.sh "$CLI" "$ENCRYPTION" "$KEY_OPTS"

$BASEDIR/common/sanity-basic.sh "$BASEDIR"
test -n "$CEPHFS" && $BASEDIR/common/sanity-cephfs.sh "$BASEDIR"

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
echo "WWWW"
echo "NFS-Ganesha sanity checks OK"

if [ -z "$MINI" ] ; then
    run_stage_0 "$CLI"
    echo "WWWW"
    echo "re-run of Stage 0 OK"
fi
