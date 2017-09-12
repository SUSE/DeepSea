#
# This file is part of the DeepSea integration test suite
#

BASEDIR=$(pwd)
source $BASEDIR/common/helper.sh
source $BASEDIR/common/json.sh
source $BASEDIR/common/rbd.sh
source $BASEDIR/common/rgw.sh

# determine hostname of Salt Master
MASTER_MINION_SLS=/srv/pillar/ceph/master_minion.sls
if test -s $MASTER_MINION_SLS ; then
    SALT_MASTER=$(cat $MASTER_MINION_SLS | \
                 sed 's/.*master_minion:[[:blank:]]*\(\w\+\)[[:blank:]]*/\1/' | \
                 grep -v '^$')
else
    echo "Could not determine the Salt Master from DeepSea pillar data. Is DeepSea installed?"
    exit 1
fi

# set deepsea_minions to * - see https://github.com/SUSE/DeepSea/pull/526
echo "deepsea_minions: '*'" > /srv/pillar/ceph/deepsea_minions.sls

# get list of minions
if type salt-key > /dev/null 2>&1; then
    MINIONS_LIST=$(salt-key -L -l acc | grep -v '^Accepted Keys')
else
    echo "Cannot find salt-key. Is Salt installed? Is this running on the Salt Master?"
    exit 1
fi

export DEV_ENV='true'


#
# functions for processing command-line arguments
#

function assert_enhanced_getopt {
    set +e
    echo -n "Running 'getopt --test'... "
    getopt --test > /dev/null
    if [ $? -ne 4 ]; then
        echo "FAIL"
        echo "This script requires enhanced getopt. Bailing out."
        exit 1
    fi
    echo "PASS"
    set -e
}

#
# functions for setting up the Salt Master node so it can run these tests
#

function install_deps {
  echo "Installing dependencies on the Salt Master node"
  DEPENDENCIES="jq
  "
  zypper --non-interactive --no-gpg-checks refresh
  for d in $DEPENDENCIES ; do
    zypper --non-interactive install --no-recommends $d
  done
}


#
# functions for running the DeepSea stages
#

function run_stage_0 {
  _run_stage 0 "$@"
}

function run_stage_1 {
  _run_stage 1 "$@"
}

function run_stage_2 {
  _run_stage 2 "$@"
  salt_pillar_items
}

function run_stage_3 {
  cat_global_conf
  _run_stage 3 "$@"
  salt_cmd_run_lsblk
  cat_ceph_conf
  admin_auth_status
}

function run_stage_4 {
  _run_stage 4 "$@"
}

function run_stage_5 {
  _run_stage 5 "$@"
}


#
# functions for generating ceph.conf
# see https://github.com/SUSE/DeepSea/tree/master/srv/salt/ceph/configuration/files/ceph.conf.d
#

function ceph_conf_small_cluster {
  local STORAGENODES=$(json_storage_nodes)
  test ! -z "$STORAGENODES"
  if [ "x$STORAGENODES" = "x1" ] ; then
    # 1 node, 2 OSDs
    echo "Adjusting ceph.conf for operation with 1 storage node"
    cat <<EOF >> /srv/salt/ceph/configuration/files/ceph.conf.d/global.conf
mon pg warn min per osd = 16
osd pool default size = 2
osd crush chooseleaf type = 0 # failure domain == osd
EOF
  elif [ "x$STORAGENODES" = "x2" ] ; then
    # 2 nodes, 4 OSDs
    echo "Adjusting ceph.conf for operation with 2 storage nodes"
    cat <<EOF >> /srv/salt/ceph/configuration/files/ceph.conf.d/global.conf
mon pg warn min per osd = 8
osd pool default size = 2
EOF
  else
    echo "Three or more storage nodes; not adjusting ceph.conf"
    # TODO: look up default value of "mon pg warn min per osd"
  fi
}

function ceph_conf_mon_allow_pool_delete {
    echo "Adjusting ceph.conf to allow pool deletes"
    cat <<EOF >> /srv/salt/ceph/configuration/files/ceph.conf.d/global.conf
mon allow pool delete = true
EOF
}

#
# functions for generating osd profiles
#

function proposal_populate_dmcrypt {
    salt-run proposal.populate encryption='dmcrypt' name='dmcrypt'
}

#
# functions for generating policy.cfg
#

function policy_cfg_encryption {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Hardware Profile
profile-dmcrypt/cluster/*.sls
profile-dmcrypt/stack/default/ceph/minions/*yml
EOF
}

function policy_cfg_base {
  cat <<EOF > /srv/pillar/ceph/proposals/policy.cfg
# Cluster assignment
cluster-ceph/cluster/*.sls
# Common configuration
config/stack/default/global.yml
config/stack/default/ceph/cluster.yml
# Role assignment - master
role-master/cluster/${SALT_MASTER}*.sls
# Role assignment - admin
role-admin/cluster/*.sls
# Role assignment - mon
role-mon/cluster/*.sls slice=[:1]
role-mgr/cluster/*.sls slice=[:1]
role-mon/stack/default/ceph/minions/*.yml slice=[:1]
EOF
}

function policy_cfg_no_client {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Hardware Profile
profile-default/cluster/*.sls
profile-default/stack/default/ceph/minions/*yml
EOF
}


function policy_cfg_client {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Hardware Profile
profile-default/cluster/*.sls slice=[:-1]
profile-default/stack/default/ceph/minions/*yml slice=[:-1]
EOF
}

function policy_cfg_mds {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - mds
role-mds/cluster/*.sls slice=[:-1]
EOF
}

# NOTE: RGW does not coexist well with openATTIC
function policy_cfg_rgw {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - rgw (first node)
role-rgw/cluster/*.sls slice=[:1]
EOF
}

function policy_cfg_rgw_ssl {
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - rgw (first node)
role-rgw/cluster/*.sls slice=[:1]
role-rgw-ssl/cluster/*.sls slice=[:1]
EOF
}



function policy_cfg_igw {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - igw (first node)
role-igw/cluster/*.sls slice=[:1]
EOF
}

function policy_cfg_nfs_ganesha {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - NFS-Ganesha (first node)
role-ganesha/cluster/*.sls slice=[:1]
EOF
}


#
# functions that print status information
#

function cat_salt_config {
  cat /etc/salt/master
  cat /etc/salt/minion
}

function cat_policy_cfg {
  cat /srv/pillar/ceph/proposals/policy.cfg
}

function salt_pillar_items {
  salt '*' pillar.items
}

function salt_pillar_get_roles {
  salt '*' pillar.get roles
}

function salt_cmd_run_lsblk {
  salt '*' cmd.run lsblk
}

function cat_global_conf {
  cat /srv/salt/ceph/configuration/files/ceph.conf.d/global.conf || true
}

function cat_ceph_conf {
  cat /etc/ceph/ceph.conf
}

function admin_auth_status {
  ceph auth get client.admin
  ls -l /etc/ceph/ceph.client.admin.keyring
  cat /etc/ceph/ceph.client.admin.keyring
}

function ceph_cluster_status {
  ceph pg stat -f json-pretty
  _grace_period 1
  ceph health detail -f json-pretty
  _grace_period 1
  ceph osd tree
  _grace_period 1
  ceph osd pool ls detail -f json-pretty
  _grace_period 1
  ceph -s
}


#
# core validation tests
#

function ceph_version_sanity_test {
  rpm -q ceph
  local RPM_NAME=$(rpm -q ceph)
  local RPM_CEPH_VERSION=$(perl -e '"'"$RPM_NAME"'" =~ m/ceph-(\d+\.\d+\.\d+)(\-|\+)/; print "$1\n";')
  echo "According to RPM, the ceph upstream version is $RPM_CEPH_VERSION"
  ceph --version
  local BUFFER=$(ceph --version)
  local CEPH_CEPH_VERSION=$(perl -e '"'"$BUFFER"'" =~ m/ceph version (\d+\.\d+\.\d+)(\-|\+)/; print "$1\n";')
  echo "According to \"ceph --version\", the ceph upstream version is $CEPH_CEPH_VERSION"
  test "$RPM_CEPH_VERSION" = "$CEPH_CEPH_VERSION"
}

function ceph_health_test {
  local LOGFILE=/tmp/ceph_health_test.log
  echo "Waiting up to 15 minutes for HEALTH_OK..."
  salt -C 'I@roles:master' wait.until status=HEALTH_OK timeout=900 check=1 | tee $LOGFILE
  # last line: determines return value of function
  ! grep -q 'Timeout expired' $LOGFILE
}

function cephfs_mount_and_sanity_test {
  #
  # run cephfs mount test script on the client node
  # mounts cephfs in /mnt, touches a file, asserts that it exists
  #
  local TESTSCRIPT=/tmp/cephfs_test.sh
  local CLIENTNODE=$(_client_node)
  cat << 'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "cephfs mount test script running as $(whoami) on $(hostname --fqdn)"
TESTMONS=$(ceph-conf --lookup 'mon_initial_members' | tr -d '[:space:]')
TESTSECR=$(grep 'key =' /etc/ceph/ceph.client.admin.keyring | awk '{print $NF}')
echo "MONs: $TESTMONS"
echo "admin secret: $TESTSECR"
test -d /mnt
mount -t ceph ${TESTMONS}:/ /mnt -o name=admin,secret="$TESTSECR"
touch /mnt/bubba
test -f /mnt/bubba
umount /mnt
echo "Result: OK"
EOF
  # FIXME: assert no MDS running on $CLIENTNODE
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE
}

function iscsi_kludge {
  #
  # apply kludge to work around bsc#1049669
  #
  local TESTSCRIPT=/tmp/iscsi_kludge.sh
  local IGWNODE=$(_first_x_node igw)
  cat << 'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "igw kludge script running as $(whoami) on $(hostname --fqdn)"
sed -i -e 's/\("host": "target[[:digit:]]\+\)"/\1.teuthology"/' /tmp/lrbd.conf
cat /tmp/lrbd.conf
source /etc/sysconfig/lrbd; lrbd -v $LRBD_OPTIONS -f /tmp/lrbd.conf
systemctl restart lrbd.service
systemctl status -l lrbd.service
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $IGWNODE
}

function igw_info {
  #
  # peek at igw information on the igw node
  #
  local TESTSCRIPT=/tmp/igw_info.sh
  local IGWNODE=$(_first_x_node igw)
  cat << 'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "igw info script running as $(whoami) on $(hostname --fqdn)"
rpm -q lrbd || true
lrbd --output || true
ls -lR /sys/kernel/config/target/ || true
netstat --tcp --listening --numeric-ports
echo "See 3260 there?"
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $IGWNODE
}

function iscsi_mount_and_sanity_test {
  #
  # run iscsi mount test script on the client node
  # mounts iscsi in /mnt, touches a file, asserts that it exists
  #
  local TESTSCRIPT=/tmp/iscsi_test.sh
  local CLIENTNODE=$(_client_node)
  local IGWNODE=$(_first_x_node igw)
  cat << EOF > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
zypper --non-interactive --no-gpg-checks refresh
zypper --non-interactive install --no-recommends open-iscsi multipath-tools
systemctl start iscsid.service
sleep 5
systemctl status -l iscsid.service
iscsiadm -m discovery -t st -p $IGWNODE
iscsiadm -m node -L all
systemctl start multipathd.service
sleep 5
systemctl status -l multipathd.service
ls -lR /dev/mapper
ls -l /dev/disk/by-path
ls -l /dev/disk/by-*id
multipath -ll
mkfs -t xfs /dev/dm-0
test -d /mnt
mount /dev/dm-0 /mnt
df -h /mnt
touch /mnt/bubba
test -f /mnt/bubba
umount /mnt
echo "Result: OK"
EOF
  # FIXME: assert script not running on the iSCSI gateway node
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE
}
