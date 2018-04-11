#
# This file is part of the DeepSea integration test suite
#
# It *must* be called like so:
#
#     source $BASEDIR/common/common.sh $BASEDIR
#

BASEDIR=${1}
source $BASEDIR/common/helper.sh
source $BASEDIR/common/json.sh
source $BASEDIR/common/nfs-ganesha.sh
source $BASEDIR/common/rbd.sh
source $BASEDIR/common/rgw.sh

function global_test_setup {
    MASTER_MINION_SLS=/srv/pillar/ceph/master_minion.sls
    if test -s $MASTER_MINION_SLS ; then
        SALT_MASTER=$(cat $MASTER_MINION_SLS | \
                     sed 's/.*master_minion:[[:blank:]]*\(\w\+\)[[:blank:]]*/\1/' | \
                     grep -v '^$')
        export SALT_MASTER
    else
        echo "WWWW"
        echo "Could not determine the Salt Master from DeepSea pillar data. Is DeepSea installed?"
        exit 1
    fi
    
    # show which repos are active/enabled
    zypper lr -upEP
    
    # show salt RPM version in log and fail if salt is not installed
    rpm -q salt-master
    rpm -q salt-minion
    rpm -q salt-api
    
    # show deepsea RPM version in case deepsea was installed from RPM
    rpm -q deepsea || true
    
    # set deepsea_minions to * - see https://github.com/SUSE/DeepSea/pull/526
    # (otherwise we would have to set deepsea grain on all minions)
    echo "deepsea_minions: '*'" > /srv/pillar/ceph/deepsea_minions.sls
    cat /srv/pillar/ceph/deepsea_minions.sls
    
    echo "WWWW get list of minions"
    if type salt-key > /dev/null 2>&1; then
        MINIONS_LIST=$(salt-key -L -l acc | grep -v '^Accepted Keys')
        echo $MINIONS_LIST
        export MINIONS_LIST
    else
        echo "Cannot find salt-key. Is Salt installed? Is this running on the Salt Master?"
        exit 1
    fi
}


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

function zypper_ref {
    set +x
    for delay in 60 60 60 60 ; do
        zypper --non-interactive --gpg-auto-import-keys refresh && break
        sleep $delay
    done
    set -x
}

function install_deps {
    echo "Installing dependencies on the Salt Master node"
    local DEPENDENCIES="jq
    "
    zypper_ref
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
  salt '*' cmd.run "for delay in 60 60 60 60 ; do sudo zypper --non-interactive --gpg-auto-import-keys refresh && break ; sleep $delay ; done"
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

function change_rgw_conf {
    cat <<EOF >> /srv/salt/ceph/configuration/files/ceph.conf.d/rgw.conf
foo = bar
EOF
}

function change_osd_conf {
    cat <<EOF >> /srv/salt/ceph/configuration/files/ceph.conf.d/osd.conf
foo = bar
EOF
}

function change_mon_conf {
    cat <<EOF >> /srv/salt/ceph/configuration/files/ceph.conf.d/mon.conf
foo = bar
EOF
}

function ceph_conf_adjustments {
    local DASHBOARD=${1}
    cat <<EOF >> /srv/salt/ceph/configuration/files/ceph.conf.d/global.conf
mon allow pool delete = true
keyring = /etc/ceph/ceph.client.admin.keyring
EOF
    if [ -n "$DASHBOARD" ] ; then
      echo "Adjusting ceph.conf for deployment of dashboard MGR module"
    cat <<EOF >> /srv/salt/ceph/configuration/files/ceph.conf.d/mon.conf
mgr initial modules = dashboard
EOF
    fi
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

#
# functions for generating osd profiles
#

function proposal_populate_dmcrypt {
  salt-run proposal.populate encryption='dmcrypt' name='dmcrypt'
}

#
# functions for testing ceph.restart orchestration
#

function restart_services {
  salt-run state.orch ceph.restart
}

function mon_restarted {
  local expected_return=$1
  local mon_hosts=$(salt --static --out json -C "I@roles:mon" test.ping | jq -r 'keys[]')
  set +e
  for minion in ${mon_hosts}; do
    salt "${minion}*" cmd.shell "journalctl -u ceph-mon@*" | grep -i terminated
    test $? = ${expected_return}
  done
  set -e
}

function osd_restarted {
    local expected_return=$1
    osd_hosts=$(salt --static --out json -C "I@roles:storage" test.ping | jq -r 'keys[]')
    set +e
    for host in ${osd_hosts}; do
        osds=$(salt --static --out json ${host} osd.list | jq .[][])
        for osd in ${osds}; do
            salt ${host} cmd.shell "journalctl -u ceph-osd@${osd}" | grep -i terminated
            test $? = ${expected_return}
        done
    done
    set -e
}

function rgw_restarted {
  local expected_return=$1
  rgw_hosts=$(salt --static --out json -C "I@roles:rgw" test.ping | jq -r 'keys[]')
  set +e
  for host in ${rgw_hosts}; do
    salt ${host} cmd.shell "journalctl -u ceph-radosgw@*" | grep -i terminated
    test $? = ${expected_return}
  done
  set -e
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
EOF
}

function policy_cfg_mon_flex {
  local CLUSTER_NODES=${1}
  test -n "$CLUSTER_NODES"
  if [ "$CLUSTER_NODES" -eq 1 ] ; then
    echo "Only one node in cluster; deploying 1 mon and 1 mgr"
    policy_cfg_one_mon
  elif [ "$CLUSTER_NODES" -eq 2 ] ; then
    echo "2-node cluster; deploying 1 mon and 1 mgr"
    policy_cfg_one_mon
  elif [ "$CLUSTER_NODES" -ge 3 ] ; then
    policy_cfg_three_mons
  else
    echo "Unexpected number of nodes ->$CLUSTER_NODES<-: bailing out!"
    exit 1
  fi
}

function policy_cfg_one_mon {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - 1 mon, 1 mgr
role-mon/cluster/*.sls slice=[:1]
role-mon/stack/default/ceph/minions/*.yml slice=[:1]
role-mgr/cluster/*.sls slice=[:1]
EOF
}

function policy_cfg_three_mons {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - 3 mons, 3 mgrs
role-mon/cluster/*.sls slice=[:3]
role-mon/stack/default/ceph/minions/*.yml slice=[:3]
role-mgr/cluster/*.sls slice=[:3]
EOF
}

function policy_cfg_storage {
  # first argument is number of non-storage ("client") nodes; defaults to 0
  # second argument controls whether OSDs are encrypted; default not encrypted
  local CLIENTS=$1
  test -z "$CLIENTS" && CLIENTS="0"
  local ENCRYPTION=$2
  local PROFILE="default"

  if [ -n "$ENCRYPTION" ] ; then
     PROFILE="dmcrypt"
  fi

  if [ "$CLIENTS" -eq 0 ] ; then
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Hardware Profile
profile-$PROFILE/cluster/*.sls
profile-$PROFILE/stack/default/ceph/minions/*yml
EOF
  elif [ "$CLIENTS" -ge 1 ] ; then
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Hardware Profile
profile-$PROFILE/cluster/*.sls slice=[:-$CLIENTS]
profile-$PROFILE/stack/default/ceph/minions/*yml slice=[:-$CLIENTS]
EOF
  else
    echo "Unexpected number of clients ->$CLIENTS<-; bailing out!"
  fi
}

function policy_cfg_mds {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - mds (all but last node)
role-mds/cluster/*.sls slice=[:-1]
EOF
}

function policy_cfg_rgw {
  local SSL=$1
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - rgw (first node)
role-rgw/cluster/*.sls slice=[:1]
EOF
  if [ -n $SSL ] ; then
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
role-rgw-ssl/cluster/*.sls slice=[:1]
EOF
  fi
}

function policy_cfg_nfs_ganesha {
  local TOTALNODES=$(json_total_nodes)
  test -n "$TOTALNODES"
  if [ "$TOTALNODES" -eq 1 ] ; then
    echo "Only one node in cluster; nfs-ganesha role on that node"
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - ganesha
role-ganesha/cluster/*.sls slice=[:1]
EOF
  elif [ "$TOTALNODES" -eq 2 ] ; then
    echo "Two nodes in cluster; deploying nfs-ganesha on first node"
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - ganesha
role-ganesha/cluster/*.sls slice=[:1]
EOF
  elif [ "$TOTALNODES" -eq 3 ] ; then
    echo "Three nodes in cluster; deploying nfs-ganesha on second node"
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - ganesha (third node)
role-ganesha/cluster/*.sls slice=[1:2]
EOF
  elif [ "$TOTALNODES" -ge 4 ] ; then
    echo "Four or more nodes in cluster; deploying nfs-ganesha on third node"
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - ganesha (fourth node)
role-ganesha/cluster/*.sls slice=[2:3]
EOF
  else
    echo "Unexpected number of nodes ->$TOTALNODES<-: bailing out!"
    exit 1
  fi
}


#
# functions for creating pools
#

function pgs_per_pool {
  local TOTALPOOLS=$1
  test -n "$TOTALPOOLS"
  local TOTALOSDS=$(json_total_osds)
  test -n "$TOTALOSDS"
  # given the total number of pools and OSDs,
  # assume triple replication and equal number of PGs per pool
  # and aim for 100 PGs per OSD
  let "TOTALPGS = $TOTALOSDS * 100"
  let "PGSPEROSD = $TOTALPGS / $TOTALPOOLS / 3"
  echo $PGSPEROSD
}

function create_pool {
  # Special-purpose function for creating pools incrementally. For example,
  # if your test case needs 2 pools "foo" and "bar", but you cannot create
  # them all at once for some reason. Otherwise, use create_all_pools_at_once.
  #
  # sample usage:
  #
  # create_pool foo 2
  # ... do something ...
  # create_pool bar 2
  # ... do something else ...
  #
  local POOLNAME=$1
  test -n "$POOLNAME"
  local TOTALPOOLS=$2
  test -n "$TOTALPOOLS"
  local PGSPERPOOL=$(pgs_per_pool $TOTALPOOLS)
  ceph osd pool create $POOLNAME $PGSPERPOOL $PGSPERPOOL replicated
}

function create_all_pools_at_once {
  # sample usage: create_all_pools_at_once foo bar
  local TOTALPOOLS="${#@}"
  local PGSPERPOOL=$(pgs_per_pool $TOTALPOOLS)
  for POOLNAME in "$@"
  do
      ceph osd pool create $POOLNAME $PGSPERPOOL $PGSPERPOOL replicated
  done
  ceph osd pool ls detail
}


#
# functions that print status information
#

function cat_deepsea_log {
  cat /var/log/deepsea.log
}

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
  salt '*' cmd.run "cat /etc/ceph/ceph.conf"
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

function ceph_health_test {
  local LOGFILE=/tmp/ceph_health_test.log
  echo "Waiting up to 15 minutes for HEALTH_OK..."
  salt -C 'I@roles:master' wait.until status=HEALTH_OK timeout=900 check=1 | tee $LOGFILE
  # last line: determines return value of function
  ! grep -q 'Timeout expired' $LOGFILE
}

function salt_api_test {
  echo "Salt API test: BEGIN"
  systemctl status salt-api.service
  curl http://${SALT_MASTER}:8000/ | python3 -m json.tool
  echo "Salt API test: END"
}

function configure_all_OSDs_to_filestore {
	salt-run proposal.populate format=filestore name=filestore 
	chown salt:salt /srv/pillar/ceph/proposals/policy.cfg
	sed -i 's/profile-default/profile-filestore/g' /srv/pillar/ceph/proposals/policy.cfg
}

function verify_OSD_type {
    # checking with 'ceph osd metadata' command
    # 1st input argument: type 'filestore' or 'bluestore'
    # 2nd input argument: OSD ID 
    osd_type=$(ceph osd metadata $2 -f json-pretty | jq '.osd_objectstore')
    if [[ $osd_type != \"$1\" ]]
        then 
        echo "Error: Object store type is not $1 for OSD.ID : $2"
        exit 1
    else
        echo OSD.${2} $osd_type
    fi
}

function check_OSD_type {  
    # expecting as argument 'filestore' or 'bluestore' 
    for i in $(ceph osd ls);do verify_OSD_type $1 $i;done
}

function migrate_to_bluestore {
	salt-run state.orch ceph.migrate.policy
	sed -i 's/profile-filestore/migrated-profile-filestore/g' /srv/pillar/ceph/proposals/policy.cfg
	salt-run disengage.safety
	salt-run state.orch ceph.migrate.osds
}

function disable_restart_in_stage_0 {
	cp /srv/salt/ceph/stage/prep/master/default.sls /srv/salt/ceph/stage/prep/master/default-orig.sls 
	cp /srv/salt/ceph/stage/prep/master/default-update-no-reboot.sls /srv/salt/ceph/stage/prep/master/default.sls 
	cp /srv/salt/ceph/stage/prep/minion/default.sls /srv/salt/ceph/stage/prep/minion/default-orig.sls 
	cp /srv/salt/ceph/stage/prep/minion/default-update-no-reboot.sls /srv/salt/ceph/stage/prep/minion/default.sls
}
