#
# This file is part of the DeepSea integration test suite
#

NFS_MOUNTPOINT=/root/mnt

function _nfs_ganesha_node {
  _first_x_node ganesha
}

function nfs_ganesha_no_root_squash {
  local GANESHAJ2=/srv/salt/ceph/ganesha/files/ganesha.conf.j2
  sed -i '/Access_Type = RW;/a \\tSquash = No_root_squash;' $GANESHAJ2
}

#
# Since we don't seem to be using NFSv4, the effect of this option is unclear
#
function nfs_ganesha_no_grace_period {
  local GANESHAJ2=/srv/salt/ceph/ganesha/files/ganesha.conf.j2
  cat <<EOF >>$GANESHAJ2
NFSv4 {Graceless = True}
EOF
}

function nfs_ganesha_debug_log {
  local GANESHANODE=$(_nfs_ganesha_node)
  local TESTSCRIPT=/tmp/test-nfs-ganesha.sh
  cat <<EOF > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "nfs-ganesha debug log script running as $(whoami) on $(hostname --fqdn)"
sed -i 's/NIV_EVENT/NIV_DEBUG/g' /etc/sysconfig/nfs-ganesha
cat /etc/sysconfig/nfs-ganesha
rm -rf /var/log/ganesha/ganesha.log
systemctl restart nfs-ganesha.service
systemctl is-active nfs-ganesha.service
rpm -q nfs-ganesha
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $GANESHANODE
}

function nfs_ganesha_cat_config_file {
  salt -C 'I@roles:ganesha' cmd.run 'cat /etc/ganesha/ganesha.conf'
}

#function nfs_ganesha_showmount_loop {
#  local TESTSCRIPT=/tmp/test-nfs-ganesha.sh
#  salt -C 'I@roles:ganesha' cmd.run "while true ; do showmount -e $GANESHANODE | tee /tmp/showmount.log || true ; grep -q 'Timed out' /tmp/showmount.log || break ; done"
#}

function nfs_ganesha_mount {
  #
  # creates a mount point and mounts NFS-Ganesha export in it
  #
  local NFSVERSION=$1   # can be "3", "4", or ""
  local ASUSER=$2
  local CLIENTNODE=$(_client_node)
  local GANESHANODE=$(_nfs_ganesha_node)
  if [[ -n $3 ]];then GANESHANODE=$3;fi
  local TESTSCRIPT=/tmp/test-nfs-ganesha.sh
  salt "$CLIENTNODE" pillar.get roles
  salt "$CLIENTNODE" pkg.install nfs-client # FIXME: only works on SUSE
  cat <<EOF > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "nfs-ganesha mount test script"
test ! -e $NFS_MOUNTPOINT
mkdir $NFS_MOUNTPOINT
test -d $NFS_MOUNTPOINT
#mount -t nfs -o nfsvers=4 ${GANESHANODE}:/ $NFS_MOUNTPOINT
mount -t nfs -o ##OPTIONS## ${GANESHANODE}:/ $NFS_MOUNTPOINT
ls -lR $NFS_MOUNTPOINT
echo "Result: OK"
EOF
  if test -z $NFSVERSION ; then
      sed -i 's/##OPTIONS##/sync/' $TESTSCRIPT
  elif [ "$NFSVERSION" = "3" -o "$NFSVERSION" = "4" ] ; then
      sed -i 's/##OPTIONS##/sync,nfsvers='$NFSVERSION'/' $TESTSCRIPT
  else
      echo "Bad NFS version ->$NFS_VERSION<- Bailing out!"
      exit 1
  fi
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE $ASUSER
}

function nfs_ganesha_umount {
  local ASUSER=$1
  local CLIENTNODE=$(_client_node)
  local TESTSCRIPT=/tmp/test-nfs-ganesha-umount.sh
  cat <<EOF > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "nfs-ganesha umount test script running as $(whoami) on $(hostname --fqdn)"
umount $NFS_MOUNTPOINT
rm -rf $NFS_MOUNTPOINT
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE $ASUSER
}

function nfs_ganesha_write_test {
  #
  # NFS-Ganesha FSAL write test
  #
  local FSAL=$1
  local NFSVERSION=$2
  local CLIENTNODE=$(_client_node)
  local TESTSCRIPT=/tmp/test-nfs-ganesha-write.sh
  local APPENDAGE=""
  if [ "$FSAL" = "cephfs" ] ; then
      if [ "$NFSVERSION" = "3" ] ; then
          APPENDAGE=""
      else
          APPENDAGE="/cephfs"
      fi
  else
      APPENDAGE="/demo/demo-demo"
  fi
  local TOUCHFILE=$NFS_MOUNTPOINT$APPENDAGE/saturn
  cat <<EOF > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "nfs-ganesha write test script"
! test -e $TOUCHFILE
touch $TOUCHFILE
test -f $TOUCHFILE
rm -f $TOUCHFILE
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE
}

function nfs_ganesha_pynfs_test {
  #
  # NFS-Ganesha PyNFS test
  #
  local CLIENTNODE=$(_client_node)
  local GANESHANODE=$(_nfs_ganesha_node)
  local TESTSCRIPT=/tmp/test-nfs-ganesha-pynfs.sh
  cat <<'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR

function assert_success {
    local PYNFS_OUTPUT=$1
    test -s $PYNFS_OUTPUT
    # last line: determined return value of function
    ! grep -q FAILURE $PYNFS_OUTPUT
}

echo "nfs-ganesha PyNFS test script running as $(whoami) on $(hostname --fqdn)"
zypper --non-interactive install --no-recommends krb5-devel python3-devel
git clone --depth 1 https://github.com/supriti/Pynfs
cd Pynfs
./setup.py build
cd nfs4.0
sleep 90 # NFSv4 grace period
LOGFILE="PyNFS.out"
./testserver.py -v \
    --outfile RESULTS.out \
    --maketree GANESHANODE:/cephfs/ \
    --showomit \
    --secure \
    --rundeps \
    all \
    ganesha 2>&1 | tee $LOGFILE
#./showresults.py RESULTS.out
assert_success $LOGFILE
echo "Result: OK"
EOF
  sed -i 's/GANESHANODE/'$GANESHANODE'/' $TESTSCRIPT
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE
}


function set_NFS_HA_IP {
        HA_GANESHA_IP=$1
        echo "NFS HA IP is : " $HA_GANESHA_IP
        salt -C 'I@roles:ganesha' grains.setval NFS_HA_IP $HA_GANESHA_IP
}

function nfs_ganesha_disable_service {
        salt -C 'I@roles:ganesha' cmd.run 'systemctl disable nfs-ganesha.service'
}

function set_NFS_HA_primary_node {
  # setting one of ganesha nodes to be HA primary node
  NFS_NODE=$(_get_fqdn_from_pillar_role ganesha|head -n 1)
  salt $NFS_NODE grains.setval ceph_ganesha_HA_master_node True
}

function get_NFS_HA_IP {
        echo $(_get_salt_grain_value NFS_HA_IP|tail -n 1)
}
function nfs_ha_cluster_bootstrap {
        NFS_GANESHA_primary_node=$(_get_fqdn_from_salt_grain_key ceph_ganesha_HA_master_node)
        NFS_GANESHA_secondary_node=$(_get_fqdn_from_pillar_role ganesha|grep -v $NFS_GANESHA_primary_node)

        # establish passwordless ssh access to HA nodes
        MINION_HA_NODE_1=$NFS_GANESHA_primary_node
        MINION_HA_NODE_2=$NFS_GANESHA_secondary_node
        salt -C 'I@roles:ganesha' cmd.run "sed -i '/StrictHostKeyChecking/c\StrictHostKeyChecking no' /etc/ssh/ssh_config"
        salt $MINION_HA_NODE_1\* cmd.run 'ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa'
        salt $MINION_HA_NODE_2\* cmd.run 'ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa'
        PUB_KEY_HA_NODE_1=$(salt $MINION_HA_NODE_1 cmd.run 'cat /root/.ssh/id_rsa.pub' --out yaml|sed 's/.* ssh-rsa/ssh-rsa/g')
        PUB_KEY_HA_NODE_2=$(salt $MINION_HA_NODE_2 cmd.run 'cat /root/.ssh/id_rsa.pub' --out yaml|sed 's/.* ssh-rsa/ssh-rsa/g')
        salt $MINION_HA_NODE_1 cmd.run "echo $PUB_KEY_HA_NODE_2 >> ~/.ssh/authorized_keys"
        salt $MINION_HA_NODE_2 cmd.run "echo $PUB_KEY_HA_NODE_1 >> ~/.ssh/authorized_keys"

        # configure cluster
        HA_GANESHA_IP=$(get_NFS_HA_IP)
        salt -C 'I@roles:ganesha' cmd.run "zypper in -y ha-cluster-bootstrap"
        salt ${NFS_GANESHA_primary_node} cmd.run 'ha-cluster-init -y'
        salt ${NFS_GANESHA_secondary_node} cmd.run "ha-cluster-join -y -c $MINION_HA_NODE_1 csync2"
        salt ${NFS_GANESHA_secondary_node} cmd.run "ha-cluster-join -y -c $MINION_HA_NODE_1 ssh_merge"
        salt ${NFS_GANESHA_secondary_node} cmd.run "ha-cluster-join -y -c $MINION_HA_NODE_1 cluster"
        salt ${NFS_GANESHA_primary_node} cmd.run "crm status"
        salt ${NFS_GANESHA_primary_node} cmd.run 'crm configure primitive nfs-ganesha-server systemd:nfs-ganesha op monitor interval=30s'
        salt ${NFS_GANESHA_primary_node} cmd.run 'crm configure clone nfs-ganesha-clone nfs-ganesha-server meta interleave=true'
        salt ${NFS_GANESHA_primary_node} cmd.run "crm configure primitive ganesha-ip IPaddr2 params ip=${HA_GANESHA_IP} cidr_netmask=24 nic=eth0 op monitor interval=10 timeout=20"
        salt ${NFS_GANESHA_primary_node} cmd.run "crm configure commit"
        salt ${NFS_GANESHA_primary_node} cmd.run "crm status"
        salt -C 'I@roles:ganesha' service.status nfs-ganesha
        salt -C 'I@roles:ganesha' service.restart nfs-ganesha || echo # for some reason, first restart always fails
        salt -C 'I@roles:ganesha' service.restart nfs-ganesha || echo # for some reason, first restart always fails
        salt -C 'I@roles:ganesha' service.restart nfs-ganesha 
        salt ${NFS_GANESHA_primary_node} cmd.run "crm resource cleanup nfs-ganesha-server"
        salt ${NFS_GANESHA_primary_node} cmd.run "crm status"
}
function ha_ganesha_ip_failover {
        NFS_GANESHA_primary_node_fqdn=$(_get_fqdn_from_salt_grain_key ceph_ganesha_HA_master_node)
        NFS_GANESHA_primary_node=${NFS_GANESHA_primary_node_fqdn%%\.*}
        echo "Primary nfs-ganesha node is : " $NFS_GANESHA_primary_node_fqdn
        NFS_GANESHA_secondary_node_fqdn=$(_get_fqdn_from_pillar_role ganesha|grep -v $NFS_GANESHA_primary_node)
        NFS_GANESHA_secondary_node=${NFS_GANESHA_secondary_node_fqdn%%\.*}
        echo "Secondary nfs-ganesha node is : " $NFS_GANESHA_secondary_node_fqdn
        current_ganesha_ip_node=$(salt ${NFS_GANESHA_primary_node_fqdn} cmd.run "crm status"|grep ganesha-ip|awk '{print $4}')
        echo 'Current ganesha-ip node is :' $current_ganesha_ip_node
        if [[ $current_ganesha_ip_node == $NFS_GANESHA_primary_node ]]; then
                failover_node=$NFS_GANESHA_secondary_noden
        else
                failover_node=$NFS_GANESHA_primary_node
        fi
        salt ${NFS_GANESHA_primary_node_fqdn} cmd.run "crm resource migrate ganesha-ip $failover_node"
        sleep 3
}

