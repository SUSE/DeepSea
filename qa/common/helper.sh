# This file is part of the DeepSea integration test suite

#
# helper functions (not to be called directly from test scripts)
#

function _report_stage_failure_and_die {
  local stage_num=$1
  local stage_log_path=$2
  local number_of_failures=$3

  test -z $number_of_failures && number_of_failures="unknown number of"
  echo "********** Stage $stage_num failed with $number_of_failures failures **********"
  echo "Here comes the log:"
  cat $stage_log_path
  exit 1
}

function _run_stage {
  local stage_num=$1
  local cli=$2
  test -z "$cli" && cli="classic"
  local stage_log_path="/tmp/stage.${stage_num}.log"

  set +x
  echo ""
  echo "*********************************************"
  echo "********** Running DeepSea Stage $stage_num **********"
  echo "*********************************************"
  set -x

  # CLI case
  if [ "x$cli" = "xcli" ] ; then
      echo "using DeepSea CLI"
      deepsea \
          --log-file=/var/log/salt/deepsea.log \
          --log-level=debug \
          stage \
          run \
          ceph.stage.${stage_num} \
          --simple-output
      return
  fi

  # non-CLI ("classic") case
  echo -n "" > $stage_log_path
  salt-run --no-color state.orch ceph.stage.${stage_num} 2>&1 > $stage_log_path
  STAGE_FINISHED=$(grep -F 'Total states run' $stage_log_path)

  if [[ "$STAGE_FINISHED" ]]; then
    FAILED=$(grep -F 'Failed: ' $stage_log_path | sed 's/.*Failed:\s*//g' | head -1)
    if [[ "$FAILED" -gt "0" ]]; then
      _report_stage_failure_and_die $stage_num $stage_log_path $FAILED
    fi
    echo "********** Stage $stage_num completed successefully **********"
  else
    _report_stage_failure_and_die $stage_num $stage_log_path
  fi
}

function _client_node {
  #
  # FIXME: migrate this to "salt --static --out json ... | jq ..."
  #
  salt --no-color -C 'not I@roles:storage' test.ping | grep -o -P '^\S+(?=:)' | head -1
}

function _first_x_node {
  local ROLE=$1
  salt --no-color -C "I@roles:$ROLE" test.ping | grep -o -P '^\S+(?=:)' | head -1
}

function _run_test_script_on_node {
  local TESTSCRIPT=$1
  local TESTNODE=$2
  local ASUSER=$3
  salt-cp $TESTNODE $TESTSCRIPT $TESTSCRIPT
  local LOGFILE=/tmp/test_script.log
  if [ -z "$ASUSER" -o "x$ASUSER" = "xroot" ] ; then
    salt $TESTNODE cmd.run "sh $TESTSCRIPT" | tee $LOGFILE
  else
    salt $TESTNODE cmd.run "sudo su $ASUSER -c \"bash $TESTSCRIPT\"" | tee $LOGFILE
  fi
  local RESULT=$(grep -o -P '(?<=Result: )(OK|NOT_OK)$' $LOGFILE | head -1)
  test "x$RESULT" = "xOK"
}

function _grace_period {
  local SECONDS=$1
  echo "${SECONDS}-second grace period"
  sleep $SECONDS
}
