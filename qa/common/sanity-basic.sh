#!/bin/bash
#
# a battery of basic sanity checks applicable to any Ceph cluster
#
# takes a single argument, BASEDIR, for sourcing common/common.sh

BASEDIR=${1}
source $BASEDIR/common/common.sh

set -ex

# -----------------------------------------------------------------
# sanity_basic_ceph_status
# -----------------------------------------------------------------
#
# Description: assert that "ceph status" returns usable information
CEPH_STATUS_OUTPUT=$(ceph status --format json-pretty)
CEPH_STATUS=$(echo $CEPH_STATUS_OUTPUT | jq -r '.health.status')
test "$CEPH_STATUS" = "HEALTH_OK"

# -----------------------------------------------------------------
# sanity_basic_at_least_one_osd
# -----------------------------------------------------------------
#
# Description: assert there is at least 1 OSD in the cluster
CEPH_OSD_LS_OUTPUT=$(ceph osd ls 2>/dev/null)
NUMBER_OF_OSDS=$(echo "$CEPH_OSD_LS_OUTPUT" | wc -l)
echo "There are $NUMBER_OF_OSDS OSDs in the cluster"
test -n "$CEPH_OSD_LS_OUTPUT"
echo "The number of OSDs is greater than 1"


# -----------------------------------------------------------------
# sanity_basic_ceph_log_grep_enoent_eaccess
# -----------------------------------------------------------------
#
# Description: on a MON node, check the ceph log for certain strings
set +e
grep -rH "Permission denied" /var/log/ceph
grep -rH "No such file or directory" /var/log/ceph
set -e


# -----------------------------------------------------------------
# sanity_basic_systemd_ceph_osd_target_wants
# -----------------------------------------------------------------
#
# Description: see bsc#1051598 in which ceph-disk was omitting --runtime when
# it enabled ceph-osd@$ID.service units
#
function sanity_basic_systemd_ceph_osd_target_wants {
  local TESTSCRIPT=/tmp/test_systemd_ceph_osd_target_wants.sh
  local STORAGENODE=$(_first_x_node storage)
  cat << 'EOF' > $TESTSCRIPT
set -x
CEPH_OSD_WANTS="/systemd/system/ceph-osd.target.wants"
ETC_CEPH_OSD_WANTS="/etc$CEPH_OSD_WANTS"
RUN_CEPH_OSD_WANTS="/run$CEPH_OSD_WANTS"
ls -l $ETC_CEPH_OSD_WANTS
ls -l $RUN_CEPH_OSD_WANTS
set -e
trap 'echo "Result: NOT_OK"' ERR
echo "Asserting that there is no directory $ETC_CEPH_OSD_WANTS"
test -d "$ETC_CEPH_OSD_WANTS" && false
echo "Asserting that $RUN_CEPH_OSD_WANTS exists, is a directory, and is not empty"
test -d "$RUN_CEPH_OSD_WANTS"
test -n "$(ls --almost-all $RUN_CEPH_OSD_WANTS)"
echo "Result: OK"
EOF
    _run_test_script_on_node $TESTSCRIPT $STORAGENODE
}
sanity_basic_systemd_ceph_osd_target_wants


# -----------------------------------------------------------------
# sanity_basic_rados_write_test
# -----------------------------------------------------------------
#
# Description: write an object using "rados" CLI tool, read it back
#
#
# NOTE: function assumes the pool "write_test" already exists.
#
echo "dummy_content" > verify.txt
rados -p write_test put test_object verify.txt
rados -p write_test get test_object verify_returned.txt
test "x$(cat verify.txt)" = "x$(cat verify_returned.txt)"


# -----------------------------------------------------------------
# sanity_basic_ceph_version_test
# -----------------------------------------------------------------
#
# Description: test that ceph RPM version matches "ceph --version"
#              (for a loose definition of "matches")
function sanity_basic_ceph_version_test {
    rpm -q ceph-common
    local RPM_NAME=$(rpm -q ceph-common)
    local RPM_CEPH_VERSION=$(perl -e '"'"$RPM_NAME"'" =~ m/ceph-common-(\d+\.\d+\.\d+)(\-|\+)/; print "$1\n";')
    echo "According to RPM, the ceph upstream version is $RPM_CEPH_VERSION"
    ceph --version
    local BUFFER=$(ceph --version)
    local CEPH_CEPH_VERSION=$(perl -e '"'"$BUFFER"'" =~ m/ceph version (\d+\.\d+\.\d+)(\-|\+)/; print "$1\n";')
    echo "According to \"ceph --version\", the ceph upstream version is $CEPH_CEPH_VERSION"
    test "$RPM_CEPH_VERSION" = "$CEPH_CEPH_VERSION"
}
sanity_basic_ceph_version_test

echo "sanity checks OK"
