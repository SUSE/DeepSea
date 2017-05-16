#!/bin/bash -ex
#
# DeepSea integration test workunit "basic-health-ok.sh"
#
# This script runs DeepSea stages 0-3 to deploy a Ceph cluster on all the nodes
# that have at least one external disk drive. After stage 3 completes, the
# script checks for HEALTH_OK.
#
# The script makes no assumptions beyond those listed in qa/README.
#
# On success (HEALTH_OK is reached), the script returns 0. On failure, for
# whatever reason, the script returns non-zero.
#
# The script produces verbose output on stdout, which can be captured for later
# forensic analysis.
#
# FIXME:
# - script currently tolerates HEALTH_WARN -> not good. The only HEALTH_WARN
#   outcome it should tolerate is clock skew. (We will need a special ceph.conf
#   for two-node clusters.)

SALT_MASTER=`cat /srv/pillar/ceph/master_minion.sls | \
             sed 's/.*master_minion:[[:blank:]]*\(\w\+\)[[:blank:]]*/\1/' | \
             grep -v '^$'`

MINIONS_LIST=`salt-key -L -l acc | grep -v '^Accepted Keys' | grep -v $SALT_MASTER`

export DEV_ENV='true'

function run_stage {
  local stage_num=$1

  echo ""
  echo "*********************************************"
  echo "********** Running DeepSea Stage $stage_num **********"
  echo "*********************************************"
  echo ""

  salt-run --no-color state.orch ceph.stage.${stage_num} | tee /tmp/stage.${stage_num}.log
  STAGE_FINISHED=`fgrep 'Total states run' /tmp/stage.${stage_num}.log`

  if [[ ! -z $STAGE_FINISHED ]]; then
    FAILED=`fgrep 'Failed: ' /tmp/stage.${stage_num}.log | sed 's/.*Failed:\s*//g' | head -1`
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

function gen_policy_cfg {

  cat <<EOF > /srv/pillar/ceph/proposals/policy.cfg
# Cluster assignment
cluster-ceph/cluster/*.sls
# Hardware Profile
profile-*-1/cluster/*.sls
profile-*-1/stack/default/ceph/minions/*yml
# Common configuration
config/stack/default/global.yml
config/stack/default/ceph/cluster.yml
# Role assignment
role-master/cluster/${SALT_MASTER}*.sls
EOF

  for minion in $MINIONS_LIST; do
    cat <<EOF >> /srv/pillar/ceph/proposals/policy.cfg
role-mon/cluster/${minion}*.sls
role-mon/stack/default/ceph/minions/${minion}*.yml
role-admin/cluster/${minion}*.sls
EOF
  done

}

run_stage 0
run_stage 1
gen_policy_cfg
run_stage 2
run_stage 3

ceph -s | tee /dev/stderr | grep -q 'HEALTH_OK\|HEALTH_WARN'
if [[ ! $? == 0 ]]; then
  echo "Ceph cluster is not healthy!"
  ceph -s
fi 

echo "OK"

