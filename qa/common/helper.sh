# This file is part of the DeepSea integration test suite

#
# helper functions (not to be called directly from test scripts)
#

function _report_stage_failure {
    STAGE_SUCCEEDED=""
    local stage_num=$1
    #local stage_log_path=$2
    #local number_of_failures=$3

    test -z $number_of_failures && number_of_failures="unknown number of"
    echo "********** Stage $stage_num failed with $number_of_failures failures **********"
    echo "Here comes the systemd log:"
    #cat $stage_log_path
    journalctl -r | head -n 1000
}

function _run_stage {
    local stage_num=$1

    set +x
    echo ""
    echo "*********************************************"
    echo "********** Running DeepSea Stage $stage_num **********"
    echo "*********************************************"
    set -x

    STAGE_SUCCEEDED="non-empty string"
    test -n "$CLI" && _run_stage_cli $stage_num || _run_stage_non_cli $stage_num
}

function _run_stage_cli {
    local stage_num=$1
    local deepsea_cli_output_path="/tmp/deepsea.${stage_num}.log"
    local deepsea_exit_status=""

    echo "using DeepSea CLI"
    set +e
    deepsea \
        --log-file=/var/log/salt/deepsea.log \
        --log-level=debug \
        stage \
        run \
        ceph.stage.${stage_num} \
        --simple-output \
        2>&1 | tee $deepsea_cli_output_path
    deepsea_exit_status="${PIPESTATUS[0]}"
    echo "deepsea exit status: $deepsea_exit_status"
    echo "WWWW"
    if [ "$deepsea_exit_status" = "0" ] ; then
        if grep -q -F "failed=0" $deepsea_cli_output_path ; then
            echo "********** Stage $stage_num completed successfully **********"
        else
            echo "ERROR: deepsea stage returned exit status 0, yet one or more steps failed. Bailing out!"
            _report_stage_failure $stage_num
        fi
    else
        _report_stage_failure $stage_num
    fi
    set -e
}

function _run_stage_non_cli {
    local stage_num=$1
    local stage_log_path="/tmp/stage.${stage_num}.log"

    echo -n "" > $stage_log_path
    salt-run --no-color state.orch ceph.stage.${stage_num} 2>&1 | tee $stage_log_path
    echo "WWWW"
    STAGE_FINISHED=$(grep -F 'Total states run' $stage_log_path)

    if [[ "$STAGE_FINISHED" ]]; then
      FAILED=$(grep -F 'Failed: ' $stage_log_path | sed 's/.*Failed:\s*//g' | head -1)
      if [[ "$FAILED" -gt "0" ]]; then
        _report_stage_failure $stage_num
      fi
      echo "********** Stage $stage_num completed successfully **********"
    else
      _report_stage_failure $stage_num
    fi
}

function _client_node {
    salt --static --out json -C 'not I@roles:storage' test.ping | jq -r 'keys[0]'
}

function _master_has_role {
    local ROLE=$1
    salt $(hostname) pillar.get roles
    salt $(hostname) pillar.get roles | grep -q "$1"
}

function _first_x_node {
    local ROLE=$1
    salt --static --out json -C "I@roles:$ROLE" test.ping | jq -r 'keys[0]'
}

function _run_test_script_on_node {
    local TESTSCRIPT=$1 # on success, TESTSCRIPT must output the exact string
                        # "Result: OK" on a line by itself, otherwise it will
                        # be considered to have failed
    local TESTNODE=$2
    local ASUSER=$3
    salt-cp $TESTNODE $TESTSCRIPT $TESTSCRIPT
    local LOGFILE=/tmp/test_script.log
    local STDERR_LOGFILE=/tmp/test_script_stderr.log
    if [ -z "$ASUSER" -o "x$ASUSER" = "xroot" ] ; then
      salt $TESTNODE cmd.run "sh $TESTSCRIPT" 2>$STDERR_LOGFILE | tee $LOGFILE
    else
      salt $TESTNODE cmd.run "sudo su $ASUSER -c \"bash $TESTSCRIPT\"" 2>$STDERR_LOGFILE | tee $LOGFILE
    fi
    local RESULT=$(grep -o -P '(?<=Result: )(OK)$' $LOGFILE) # since the script
                                  # is run by salt, the output appears indented
    test "x$RESULT" = "xOK" && return
    echo "The test script that ran on $TESTNODE failed. The stderr output was as follows:"
    cat $STDERR_LOGFILE
    return 1
}

function _grace_period {
    local SECONDS=$1
    echo "${SECONDS}-second grace period"
    sleep $SECONDS
}

function _root_fs_is_btrfs {
    stat -f / | grep -q 'Type: btrfs'
}
