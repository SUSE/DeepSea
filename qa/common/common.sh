#!/bin/bash -ex
#
# This file is part of the DeepSea integration test suite
#

SALT_MASTER=$(cat /srv/pillar/ceph/master_minion.sls | \
             sed 's/.*master_minion:[[:blank:]]*\(\w\+\)[[:blank:]]*/\1/' | \
             grep -v '^$')

MINIONS_LIST=$(salt-key -L -l acc | grep -v '^Accepted Keys')

export DEV_ENV='true'

function _run_stage {
  local stage_num=$1

  echo ""
  echo "*********************************************"
  echo "********** Running DeepSea Stage $stage_num **********"
  echo "*********************************************"
  echo ""

  salt-run --no-color state.orch ceph.stage.${stage_num} | tee /tmp/stage.${stage_num}.log
  STAGE_FINISHED=$(grep -F 'Total states run' /tmp/stage.${stage_num}.log)

  if [[ ! -z $STAGE_FINISHED ]]; then
    FAILED=$(grep -F 'Failed: ' /tmp/stage.${stage_num}.log | sed 's/.*Failed:\s*//g' | head -1)
    if [[ "$FAILED" -gt "0" ]]; then
      echo "********** Stage $stage_num failed with $FAILED failures **********"
      echo "Check /tmp/stage.${stage_num}.log for details"
      exit 1
    fi
    echo "********** Stage $stage_num completed successefully **********"
  else
    echo "********** Stage $stage_num failed with $FAILED failures **********"
    echo "Check /tmp/stage.${stage_num}.log for details"
    exit 1
  fi
}

function run_stage_0 {
  _run_stage 0 "$@"
}

function run_stage_1 {
  _run_stage 1 "$@"
}

function run_stage_2 {
  _run_stage 2 "$@"
}

function run_stage_3 {
  _run_stage 3 "$@"
}

function run_stage_4 {
  _run_stage 4 "$@"
}

function run_stage_5 {
  _run_stage 5 "$@"
}

function gen_policy_cfg_base {
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
role-mon/stack/default/ceph/minions/*.yml slice=[:1]
EOF
}

function gen_policy_cfg_no_client {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Hardware Profile
profile-*-1/cluster/*.sls
profile-*-1/stack/default/ceph/minions/*yml
EOF
}

function gen_policy_cfg_client {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Hardware Profile
profile-*-1/cluster/*.sls slice=[:-1]
profile-*-1/stack/default/ceph/minions/*yml slice=[:-1]
EOF
}

function gen_policy_cfg_mds {
  cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
# Role assignment - mds
role-mds/cluster/*.sls slice=[:-1]
EOF
}

function cat_policy_cfg {
  cat /srv/pillar/ceph/proposals/policy.cfg
}

function ceph_health_test {
  ceph -s | tee /dev/stderr | grep -q 'HEALTH_OK\|HEALTH_WARN'
}

function _client_node {
  #
  # FIXME: migrate this to "salt --static --out json ... | jq ..."
  #
  salt --no-color -C 'not I@roles:storage' test.ping | grep -o -P '^\S+(?=:)' | head -1
}

function _mds_node {
  salt --no-color -C 'I@roles:mds' test.ping | grep -o -P '^\S+(?=:)' | head -1
}

function cephfs_mount_and_sanity_test {
  #
  # run cephfs mount test script on the client node
  # mounts cephfs in /mnt, touches a file, asserts that it exists
  #
  local TESTSCRIPT=/tmp/cephfs_test.sh
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
  local CLIENTNODE=$(_client_node)
  # FIXME: assert no MDS running on $CLIENTNODE
  salt-cp $CLIENTNODE $TESTSCRIPT $TESTSCRIPT
  local LOGFILE=/tmp/cephfs_test.log
  salt $CLIENTNODE cmd.run "sh $TESTSCRIPT" | tee $LOGFILE
  local RESULT=$(grep -o -P '(?<=Result: )(OK|NOT_OK)$' $LOGFILE | head -1)
  test "x$RESULT" = "xOK"
}

