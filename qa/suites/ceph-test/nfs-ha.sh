#!/bin/bash
#
# DeepSea integration test "suites/ceph-test/nfs-ha.sh"
#
# This script runs DeepSea stages 0-4 to deploy a Ceph cluster with NFS-Ganesha.
# After stage 4 completes, it setup NFS HA, perform basic mount and R/W NFS client test. 
# Also failover of HA IP is triggered and client tests are done again. 
#
# ** IMPORTANT ** Mandatory argument is IP address of NFS HA - free virtual, not used IP addr 
# EXAMPLE: ./suites/ceph-test/nfs-ha.sh 192.168.100.100 
# Minumum number of nodes is 3 : 2x NFS-Ganesha nodes and 1x client node. 
# REQUIREMENT: ha-cluster-bootstrap packege is available 
#
# On success, the script returns 0. On failure, for whatever reason, the script
# returns non-zero.
#
# The script produces verbose output on stdout, which can be captured for later
# forensic analysis.

set -ex
BASEDIR=$(pwd)
source $BASEDIR/common/common.sh
source $BASEDIR/common/nfs-ganesha.sh

if [ $# == 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi # no input argument 

install_deps
cat_salt_config
run_stage_0
salt_api_test
run_stage_1
policy_cfg_base
policy_cfg_mon_flex
policy_cfg_mds
policy_cfg_rgw
rgw_demo_users
policy_cfg_nfs_ganesha 2 # will deploy 2 NFS-Ganesha nodes 
policy_cfg_storage 1 # last node will be "client" (not storage)
cat_policy_cfg  
run_stage_2
ceph_conf_small_cluster
run_stage_3
ceph_cluster_status
create_all_pools_at_once cephfs_data cephfs_metadata
nfs_ganesha_no_root_squash
run_stage_4
ceph_health_test
nfs_ganesha_cat_config_file
nfs_ganesha_debug_log
# NFS_HA
set_NFS_HA_IP $1
nfs_ganesha_disable_service
set_NFS_HA_primary_node
nfs_ha_cluster_bootstrap
sleep 5
for v in "" "3" "4" ; do nfs_ganesha_mount "$v" root $1; sleep 5; nfs_ganesha_umount root;done 
ha_ganesha_ip_failover
salt -C 'I@roles:ganesha' service.status nfs-ganesha
sleep 5
for v in "" "3" "4" ; do nfs_ganesha_mount "$v" root $1; sleep 5; nfs_ganesha_umount root;done 
ha_ganesha_ip_failover
salt -C 'I@roles:ganesha' service.status nfs-ganesha
sleep 5
for v in "" "3" "4" ; do nfs_ganesha_mount "$v" root $1; sleep 5; nfs_ganesha_umount root;done 

echo "OK"

