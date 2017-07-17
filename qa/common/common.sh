#
# This file is part of the DeepSea integration test suite
#

BASEDIR=$(pwd)
source $BASEDIR/common/helper.sh
source $BASEDIR/common/json.sh
source $BASEDIR/common/rbd.sh

SALT_MASTER=$(cat /srv/pillar/ceph/master_minion.sls | \
             sed 's/.*master_minion:[[:blank:]]*\(\w\+\)[[:blank:]]*/\1/' | \
             grep -v '^$')


MINIONS_LIST=$(salt-key -L -l acc | grep -v '^Accepted Keys')

export DEV_ENV='true'


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
# functions for generating policy.cfg
#

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
profile-*-1/cluster/*.sls
profile-*-1/stack/default/ceph/minions/*yml
EOF
}

function policy_cfg_client {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Hardware Profile
profile-*-1/cluster/*.sls slice=[:-1]
profile-*-1/stack/default/ceph/minions/*yml slice=[:-1]
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

function ceph_cluster_status {
  ceph osd tree
  ceph osd pool ls detail
  ceph -s
}


#
# core validation tests
#

function ceph_health_test {
  local LOGFILE=/tmp/ceph_health_test.log
  echo "Waiting up to 15 minutes for HEALTH_OK..."
  salt -C 'I@roles:master' wait.until status=HEALTH_OK timeout=900 check=1 | tee $LOGFILE
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

function rgw_curl_test {
  local TESTSCRIPT=/tmp/rgw_test.sh
  cat << 'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "rgw curl test running as $(whoami) on $(hostname --fqdn)"
RGWNODE=$(salt --no-color -C "I@roles:rgw" test.ping | grep -o -P '^\S+(?=:)' | head -1)
zypper --non-interactive --no-gpg-checks refresh
zypper --non-interactive install --no-recommends curl libxml2-tools
RGWXMLOUT=/tmp/rgw_test.xml
curl $RGWNODE > $RGWXMLOUT
test -f $RGWXMLOUT
xmllint $RGWXMLOUT
grep anonymous $RGWXMLOUT
rm -f $RGWXMLOUT
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $SALT_MASTER
}

