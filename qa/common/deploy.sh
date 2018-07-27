# This file is part of the DeepSea integration test suite

#
# separate file to house the deploy_ceph function
#

function report_config {
    if [ -n "$CLI" ] ; then
        echo "CLI will be used"
    else
        echo "CLI will **NOT** be used"
    fi
    test "$STORAGE_PROFILE"
    case "$STORAGE_PROFILE" in
        default)   echo "Storage profile: bluestore OSDs (default)" ; break ;;
        dmcrypt)   echo "Storage profile: encrypted bluestore OSDs" ; break ;;
        filestore) echo "Storage profile: filestore OSDs"           ; break ;;
        random)    echo "Storage profile will be chosen randomly" ; break ;;
        *) CUSTOM_STORAGE_PROFILE="$STORAGE_PROFILE" ; STORAGE_PROFILE="custom" ; echo "Storage profile: custom ($CUSTOM_STORAGE_PROFILE)" ; break ;;
    esac
    if [ -n "$MIN_NODES" ] ; then
        echo "MIN_NODES is set to $MIN_NODES"
        PROPOSED_MIN_NODES="$MIN_NODES"
    else
        echo "MIN_NODES was not set. Default is 1"
        PROPOSED_MIN_NODES=1
    fi
    if [ -n "$CLIENT_NODES" ] ; then
        echo "CLIENT_NODES is set to $CLIENT_NODES"
    else
        echo "CLIENT_NODES was not set. Default is 0"
        CLIENT_NODES=0
    fi
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

function global_test_init {
    #
    # determine hostname of Salt Master
    SALT_MASTER=$(hostname)
    #
    # show which repos are active/enabled
    zypper lr -upEP
    #
    # show salt RPM version in log and fail if salt is not installed
    rpm -q salt-master
    rpm -q salt-minion
    rpm -q salt-api
    #
    # show deepsea RPM version in case deepsea was installed from RPM
    rpm -q deepsea || true
    #
    # set deepsea_minions to * - see https://github.com/SUSE/DeepSea/pull/526
    # (otherwise we would have to set deepsea grain on all minions)
    echo "deepsea_minions: '*'" > /srv/pillar/ceph/deepsea_minions.sls
    cat /srv/pillar/ceph/deepsea_minions.sls
    #
    # get list of minions
    if type salt-key > /dev/null 2>&1; then
        MINIONS_LIST=$(salt-key -L -l acc | grep -v '^Accepted Keys')
    else
        echo "Cannot find salt-key. Is Salt installed? Is this running on the Salt Master?"
        return 1
    fi
}

function _ping_minions_until_all_respond {
    local NUM_MINIONS="$1"
    local RESPONDING=""
    for i in {1..20} ; do
        sleep 10
        RESPONDING=$(salt '*' test.ping 2>/dev/null | grep True 2>/dev/null | wc --lines)
        echo "Of $NUM_MINIONS total minions, $RESPONDING are responding"
        test "$NUM_MINIONS" -eq "$RESPONDING" && break
    done
}

function update_salt {
    # make sure we are running the latest Salt before Stage 0 starts,
    # otherwise Stage 0 will update Salt and then fail with cryptic
    # error messages
    TOTAL_NODES=$(json_total_nodes)
    salt '*' cmd.run 'zypper -n in -f python3-salt salt salt-api salt-master salt-minion'
    systemctl restart salt-api.service
    systemctl restart salt-master.service
    sleep 15
    salt '*' cmd.run 'systemctl restart salt-minion'
    _ping_minions_until_all_respond "$TOTAL_NODES"
    salt '*' saltutil.sync_all
}

function vet_nodes {
    MIN_NODES=$(($CLIENT_NODES + 1))
    if [ "$PROPOSED_MIN_NODES" -lt "$MIN_NODES" ] ; then
        echo "Proposed MIN_NODES value is too low. Need at least 1 + CLIENT_NODES"
        exit 1
    fi
    test "$PROPOSED_MIN_NODES" -gt "$MIN_NODES" && MIN_NODES="$PROPOSED_MIN_NODES"
    echo "Final MIN_NODES is $MIN_NODES"
    TOTAL_NODES=$(json_total_nodes)
    test "$TOTAL_NODES" -ge "$MIN_NODES"
    CLUSTER_NODES=$(($TOTAL_NODES - $CLIENT_NODES))
    echo "WWWW"
    echo "This script will use DeepSea to deploy a cluster of $TOTAL_NODES nodes total (including Salt Master)."
    echo "Of these, $CLIENT_NODES will be clients (nodes without any DeepSea roles except \"admin\")."
}

function ceph_cluster_running {
    ceph status >/dev/null 2>&1
}

function deploy_ceph {
    set +x
    report_config
    install_deps
    global_test_init
    update_salt
    cat_salt_config
    vet_nodes
    set -x
    test $CLUSTER_NODES -lt 4 && DEV_ENV="true"
    if ceph_cluster_running ; then
        echo "Running ceph cluster detected: skipping deploy phase"
        return 0
    fi
    disable_restart_in_stage_0
    run_stage_0 "$CLI"
    salt_api_test
    test -n "$RGW" -a -n "$SSL" && rgw_ssl_init
    run_stage_1 "$CLI"
    policy_cfg_base
    policy_cfg_mon_flex
    test -n "$MDS" && policy_cfg_mds
    test -n "$RGW" && policy_cfg_rgw
    test -n "$NFS_GANESHA" && policy_cfg_nfs_ganesha
    test -n "$NFS_GANESHA" -a -n "$RGW" && rgw_demo_users
    case "$STORAGE_PROFILE" in
        dmcrypt) proposal_populate_dmcrypt ;;
        filestore) proposal_populate_filestore ;;
        random) random_or_custom_storage_profile ;;
        custom) random_or_custom_storage_profile ;;
        default) ;;
        *) echo "Bad storage profile ->$STORAGE_PROFILE<-. Bailing out!" ; exit 1 ;;
    esac
    policy_cfg_storage
    cat_policy_cfg
    run_stage_2 "$CLI"
    ceph_conf_small_cluster
    ceph_conf_mon_allow_pool_delete
    ceph_conf_dashboard
    run_stage_3 "$CLI"
    pre_create_pools
    ceph_cluster_status
    if [ -z "$MDS" -a -z "$NFS_GANESHA" -a -z "$RGW" ] ; then
        echo "WWWW"
        echo "Stages 0-3 OK, no roles requiring Stage 4: deploy phase complete!"
        return
    fi
    test -n "$NFS_GANESHA" && nfs_ganesha_no_root_squash
    run_stage_4 "$CLI"
    if [ -n "$NFS_GANESHA" ] ; then
        nfs_ganesha_cat_config_file
        nfs_ganesha_debug_log
        echo "WWWW"
        echo "NFS-Ganesha set to debug logging"
    fi
    ceph_cluster_status
    return 0
}
