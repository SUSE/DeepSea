# This file is part of the DeepSea integration test suite

#
# separate file to house the deploy_ceph function
#

function deploy_ceph {
    echo "Entering function deploy_ceph"
    if [ -n "$CLI" ] ; then
        echo "CLI will be used"
    else
        echo "CLI will **NOT** be used"
    fi
    if [ -n "$ENCRYPTION" ] ; then
        echo "ENCRYPTION will be used"
    else
        echo "ENCRYPTION will **NOT** be used"
    fi
    assert_enhanced_getopt
    install_deps
    global_test_init
    update_salt
    cat_salt_config
    disable_restart_in_stage_0
    run_stage_0 "$CLI"
    salt_api_test
    run_stage_1 "$CLI"
    if [ -n "$ENCRYPTION" ] ; then
        proposal_populate_dmcrypt
    fi
    policy_cfg_base
    policy_cfg_mon_flex
    policy_cfg_storage 0 $ENCRYPTION # "0" means all nodes will have storage role
    cat_policy_cfg
    run_stage_2 "$CLI"
    ceph_conf_small_cluster
    run_stage_3 "$CLI"
    ceph_cluster_status
}
