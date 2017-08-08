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
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $GANESHANODE
}

function nfs_ganesha_cat_config_file {
  salt -C 'I@roles:ganesha' cmd.run 'cat /etc/ganesha/ganesha.conf'
}

function nfs_ganesha_showmount_loop {
  local TESTSCRIPT=/tmp/test-nfs-ganesha.sh
  salt -C 'I@roles:ganesha' cmd.run "while true ; do showmount -e $GANESHANODE | tee /tmp/showmount.log || true ; grep -q 'Timed out' /tmp/showmount.log || break ; done"
}

function nfs_ganesha_mount {
  #
  # creates a mount point and mounts NFS-Ganesha export in it
  #
  local ASUSER=$1
  local CLIENTNODE=$(_client_node)
  local GANESHANODE=$(_nfs_ganesha_node)
  local TESTSCRIPT=/tmp/test-nfs-ganesha.sh
  salt "$CLIENTNODE" pillar.get roles
  salt "$CLIENTNODE" pkg.install nfs-client # FIXME: only works on SUSE
  cat <<EOF > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "nfs-ganesha mount test script running as $(whoami) on $(hostname --fqdn)"
test ! -e $NFS_MOUNTPOINT
mkdir $NFS_MOUNTPOINT
test -d $NFS_MOUNTPOINT
# ************************************************
# mount the NFS export - this is prone to timeout!
# ************************************************
# NOTE: NFSv4 does not work with root, even when /etc/ganesha/ganesha.conf
# contains "Squash = No_root_squash;" line
#mount -t nfs -o nfsvers=4 ${GANESHANODE}:/ $NFS_MOUNTPOINT
mount -t nfs -o sync ${GANESHANODE}:/ $NFS_MOUNTPOINT
ls -lR $NFS_MOUNTPOINT
echo "Result: OK"
EOF
  # FIXME: assert no MDS running on $CLIENTNODE
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
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE $ASUSER
}

function nfs_ganesha_write_test {
  #
  # NFS-Ganesha FSAL write test
  #
  local FSAL=$1
  local CLIENTNODE=$(_client_node)
  local TESTSCRIPT=/tmp/test-nfs-ganesha-write.sh
  local APPENDAGE=""
  if [ "$FSAL" = "cephfs" ] ; then
      APPENDAGE="/cephfs"
  else
      APPENDAGE="/demo/demo-demo"
  fi
  local TOUCHFILE=$NFS_MOUNTPOINT$APPENDAGE/saturn
  cat <<EOF > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "nfs-ganesha write test script running as $(whoami) on $(hostname --fqdn)"
! test -e $TOUCHFILE
touch $TOUCHFILE
test -f $TOUCHFILE
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE
}
