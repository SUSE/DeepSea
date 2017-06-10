#
# This file is part of the DeepSea integration test suite
#

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
  # creates a directory /root/mnt and mounts NFS-Ganesha export in it
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
test ! -e /root/mnt
mkdir /root/mnt
test -d /root/mnt
# ************************************************
# mount the NFS export - this is prone to timeout!
# ************************************************
# NOTE: NFSv4 does not work with root, even when /etc/ganesha/ganesha.conf
# contains "Squash = No_root_squash;" line
#mount -t nfs -o nfsvers=4 ${GANESHANODE}:/ /root/mnt
mount -t nfs ${GANESHANODE}:/ /root/mnt
echo "Result: OK"
EOF
  # FIXME: assert no MDS running on $CLIENTNODE
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE $ASUSER
}

function nfs_ganesha_touch_a_file {
  #
  # touches a file, asserts that it exists, unmounts /root/mnt
  #
  local ASUSER=$1
  local CLIENTNODE=$(_client_node)
  local TESTSCRIPT=/tmp/test-nfs-ganesha.sh
  local MOUNTPOINT=/root/mnt
  local PSEUDO="/cephfs"
  local MOUNTPATH=$MOUNTPOINT
  if [ -z "$ASUSER" ] ; then
      MOUNTPATH=$MOUNTPOINT$PSEUDO
  fi
  local TOUCHFILE=$MOUNTPATH/bubba
  cat <<EOF > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "nfs-ganesha touch-a-file test script running as $(whoami) on $(hostname --fqdn)"
ls -lR $MOUNTPOINT
touch $TOUCHFILE
test -f $TOUCHFILE
umount $MOUNTPATH
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE $ASUSER
}
