# This file is part of the DeepSea integration test suite

#
# helper functions (not to be called directly from test scripts)
#

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
    salt $TESTNODE cmd.run "sudo su $ASUSER -c \"sh $TESTSCRIPT\"" | tee $LOGFILE
  fi
  local RESULT=$(grep -o -P '(?<=Result: )(OK|NOT_OK)$' $LOGFILE | head -1)
  test "x$RESULT" = "xOK"
}

