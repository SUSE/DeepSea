#
# This file is part of the DeepSea integration test suite
#
# It *must* be called like so:
#
#     source $BASEDIR/common/common.sh $BASEDIR
#

BASEDIR=${1}
source $BASEDIR/common/deploy.sh
source $BASEDIR/common/helper.sh
source $BASEDIR/common/json.sh
source $BASEDIR/common/nfs-ganesha.sh
source $BASEDIR/common/policy.sh
source $BASEDIR/common/pool.sh
source $BASEDIR/common/rbd.sh
source $BASEDIR/common/rgw.sh


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
        exit 1
    fi
}

function ping_minions_until_all_respond {
    local NUM_MINIONS="$1"
    local RESPONDING=""
    for i in {1..20} ; do
        RESPONDING=$(salt '*' test.ping 2>/dev/null | grep True 2>/dev/null | wc --lines)
        echo "Of $NUM_MINIONS total minions, $RESPONDING are responding"
        test "$NUM_MINIONS" -eq "$RESPONDING" && break
        sleep 10
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
    salt '*' cmd.run 'systemctl restart salt-minion'
    sleep 10
    ping_minions_until_all_respond "$TOTAL_NODES"
    salt '*' saltutil.sync_all
}

#
# functions for processing command-line arguments
#

function assert_enhanced_getopt {
    set +e
    echo -n "Running 'getopt --test'... "
    getopt --test > /dev/null
    if [ $? -ne 4 ]; then
        echo "FAIL"
        echo "This script requires enhanced getopt. Bailing out."
        exit 1
    fi
    echo "PASS"
    set -e
}

#
# functions for setting up the Salt Master node so it can run these tests
#

function zypper_ref {
    set +x
    for delay in 60 60 60 60 ; do
        zypper --non-interactive --gpg-auto-import-keys refresh && break
        sleep $delay
    done
    set -x
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


#
# functions for running the DeepSea stages
#

function run_stage_0 {
  _run_stage 0 "$@"
}

function run_stage_1 {
  _run_stage 1 "$@"
}

function run_stage_2 {
  salt '*' cmd.run "for delay in 60 60 60 60 ; do sudo zypper --non-interactive --gpg-auto-import-keys refresh && break ; sleep $delay ; done"
  _run_stage 2 "$@"
  salt_pillar_items
}

function run_stage_3 {
  cat_global_conf
  _run_stage 3 "$@"
  salt_cmd_run_lsblk
  cat_ceph_conf
  admin_auth_status
}

function run_stage_4 {
  _run_stage 4 "$@"
}

function run_stage_5 {
  _run_stage 5 "$@"
}


#
# functions for generating ceph.conf
# see https://github.com/SUSE/DeepSea/tree/master/srv/salt/ceph/configuration/files/ceph.conf.d
#

function change_rgw_conf {
    cat <<'EOF' >> /srv/salt/ceph/configuration/files/ceph.conf.d/rgw.conf
foo = bar
EOF
}

function change_osd_conf {
    cat <<'EOF' >> /srv/salt/ceph/configuration/files/ceph.conf.d/osd.conf
foo = bar
EOF
}

function change_mon_conf {
    cat <<'EOF' >> /srv/salt/ceph/configuration/files/ceph.conf.d/mon.conf
foo = bar
EOF
}

function ceph_conf_small_cluster {
    local STORAGENODES=$(json_storage_nodes)
    test -n "$STORAGENODES"
    if [ "$STORAGENODES" -eq 1 ] ; then
        # 1 node, 2 OSDs
        echo "Adjusting ceph.conf for operation with 1 storage node"
        cat <<'EOF' >> /srv/salt/ceph/configuration/files/ceph.conf.d/global.conf
mon pg warn min per osd = 16
osd pool default size = 2
osd crush chooseleaf type = 0 # failure domain == osd
EOF
    elif [ "$STORAGENODES" -eq 2 ] ; then
        # 2 nodes, 4 OSDs
        echo "Adjusting ceph.conf for operation with 2 storage nodes"
        cat <<'EOF' >> /srv/salt/ceph/configuration/files/ceph.conf.d/global.conf
mon pg warn min per osd = 8
osd pool default size = 2
EOF
    else
        echo "Three or more storage nodes; not adjusting ceph.conf"
        # TODO: look up default value of "mon pg warn min per osd"
    fi
}

function ceph_conf_mon_allow_pool_delete {
    echo "Adjusting ceph.conf to allow pool deletes"
    cat <<'EOF' >> /srv/salt/ceph/configuration/files/ceph.conf.d/global.conf
mon allow pool delete = true
EOF
}

function ceph_conf_dashboard {
    echo "Adjusting ceph.conf for deployment of dashboard MGR module"
    cat <<'EOF' >> /srv/salt/ceph/configuration/files/ceph.conf.d/mon.conf
mgr initial modules = dashboard
EOF
}

#
# functions for generating osd profiles
#

function proposal_populate_dmcrypt {
  salt-run proposal.populate encryption='dmcrypt' name='dmcrypt'
}

#
# functions for testing ceph.restart orchestration
#

function restart_services {
  rm -rf /srv/modules/runners/__pycache__
  salt-run state.orch ceph.restart
}

function mon_restarted {
  local expected_return=$1
  local mon_hosts=$(salt --static --out json -C "I@roles:mon" test.ping | jq -r 'keys[]')
  set +e
  for minion in ${mon_hosts}; do
    salt "${minion}*" cmd.shell "journalctl -u ceph-mon@*" | grep -i terminated
    test $? = ${expected_return}
  done
  set -e
}

function osd_restarted {
    local expected_return=$1
    osd_hosts=$(salt --static --out json -C "I@roles:storage" test.ping | jq -r 'keys[]')
    set +e
    for host in ${osd_hosts}; do
        osds=$(salt --static --out json ${host} osd.list | jq .[][])
        for osd in ${osds}; do
            salt ${host} cmd.shell "journalctl -u ceph-osd@${osd}" | grep -i terminated
            test $? = ${expected_return}
        done
    done
    set -e
}

function rgw_restarted {
  local expected_return=$1
  rgw_hosts=$(salt --static --out json -C "I@roles:rgw" test.ping | jq -r 'keys[]')
  set +e
  for host in ${rgw_hosts}; do
    salt ${host} cmd.shell "journalctl -u ceph-radosgw@*" | grep -i terminated
    test $? = ${expected_return}
  done
  set -e
}


#
# functions for creating pools
#

function pgs_per_pool {
  local TOTALPOOLS=$1
  test -n "$TOTALPOOLS"
  local TOTALOSDS=$(json_total_osds)
  test -n "$TOTALOSDS"
  # given the total number of pools and OSDs,
  # assume triple replication and equal number of PGs per pool
  # and aim for 100 PGs per OSD
  let "TOTALPGS = $TOTALOSDS * 100"
  let "PGSPEROSD = $TOTALPGS / $TOTALPOOLS / 3"
  echo $PGSPEROSD
}


#
# functions that print status information
#

function cat_deepsea_log {
  cat /var/log/deepsea.log
}

function cat_salt_config {
  cat /etc/salt/master
  cat /etc/salt/minion
}

function cat_policy_cfg {
  cat /srv/pillar/ceph/proposals/policy.cfg
}

function salt_pillar_items {
  salt '*' pillar.items
}

function salt_pillar_get_roles {
  salt '*' pillar.get roles
}

function salt_cmd_run_lsblk {
  salt '*' cmd.run lsblk
}

function cat_global_conf {
  cat /srv/salt/ceph/configuration/files/ceph.conf.d/global.conf || true
}

function cat_ceph_conf {
  salt '*' cmd.run "cat /etc/ceph/ceph.conf"
}

function admin_auth_status {
  ceph auth get client.admin
  ls -l /etc/ceph/ceph.client.admin.keyring
  cat /etc/ceph/ceph.client.admin.keyring
}

function ceph_cluster_status {
  ceph pg stat -f json-pretty
  _grace_period 1
  ceph health detail -f json-pretty
  _grace_period 1
  ceph osd tree
  _grace_period 1
  ceph osd pool ls detail -f json-pretty
  _grace_period 1
  ceph -s
}

function ceph_log_grep_enoent_eaccess {
  set +e
  grep -rH "Permission denied" /var/log/ceph
  grep -rH "No such file or directory" /var/log/ceph
  set -e
}


#
# core validation tests
#

function ceph_version_test {
# test that ceph RPM version matches "ceph --version"
# for a loose definition of "matches"
  rpm -q ceph
  local RPM_NAME=$(rpm -q ceph)
  local RPM_CEPH_VERSION=$(perl -e '"'"$RPM_NAME"'" =~ m/ceph-(\d+\.\d+\.\d+)/; print "$1\n";')
  echo "According to RPM, the ceph upstream version is $RPM_CEPH_VERSION"
  ceph --version
  local BUFFER=$(ceph --version)
  local CEPH_CEPH_VERSION=$(perl -e '"'"$BUFFER"'" =~ m/ceph version (\d+\.\d+\.\d+)/; print "$1\n";')
  echo "According to \"ceph --version\", the ceph upstream version is $CEPH_CEPH_VERSION"
  test "$RPM_CEPH_VERSION" = "$CEPH_CEPH_VERSION"
}

function ceph_health_test {
  local LOGFILE=/tmp/ceph_health_test.log
  echo "Waiting up to 15 minutes for HEALTH_OK..."
  salt -C 'I@roles:master' wait.until status=HEALTH_OK timeout=900 check=1 | tee $LOGFILE
  # last line: determines return value of function
  ! grep -q 'Timeout expired' $LOGFILE
}

function salt_api_test {
  echo "Salt API test: BEGIN"
  systemctl status salt-api.service
  curl http://${SALT_MASTER}:8000/ | python3 -m json.tool
  echo "Salt API test: END"
}

function rados_write_test {
    #
    # NOTE: function assumes the pool "write_test" already exists. Pool can be
    # created by calling e.g. "create_all_pools_at_once write_test" immediately
    # before calling this function.
    #
    local TESTSCRIPT=/tmp/test_rados_put.sh
    cat << 'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
ceph osd pool application enable write_test deepsea_qa
echo "dummy_content" > verify.txt
rados -p write_test put test_object verify.txt
rados -p write_test get test_object verify_returned.txt
test "x$(cat verify.txt)" = "x$(cat verify_returned.txt)"
echo "Result: OK"
EOF
    _run_test_script_on_node $TESTSCRIPT $SALT_MASTER
}

function cephfs_mount_and_sanity_test {
  #
  # run cephfs mount test script on the client node
  # mounts cephfs in /mnt, touches a file, asserts that it exists
  #
  local TESTSCRIPT=/tmp/cephfs_test.sh
  local CLIENTNODE=$(_client_node)
  cat << 'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "cephfs mount test script running as $(whoami) on $(hostname --fqdn)"
TESTMONS=$(ceph-conf --lookup 'mon_initial_members' | tr -d '[:space:]')
TESTSECR=$(grep 'key =' /etc/ceph/ceph.client.admin.keyring | awk '{print $NF}')
echo "MONs: $TESTMONS"
echo "admin secret: $TESTSECR"
test -d /mnt
mount -t ceph ${TESTMONS}:/ /mnt -o name=admin,secret="$TESTSECR"
touch /mnt/bubba
test -f /mnt/bubba
umount /mnt
echo "Result: OK"
EOF
  # FIXME: assert no MDS running on $CLIENTNODE
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE
}

function iscsi_kludge {
  #
  # apply kludge to work around bsc#1049669
  #
  local TESTSCRIPT=/tmp/iscsi_kludge.sh
  local IGWNODE=$(_first_x_node igw)
  cat << 'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "igw kludge script running as $(whoami) on $(hostname --fqdn)"
sed -i -e 's/\("host": "target[[:digit:]]\+\)"/\1.teuthology"/' /tmp/lrbd.conf
cat /tmp/lrbd.conf
source /etc/sysconfig/lrbd; lrbd -v $LRBD_OPTIONS -f /tmp/lrbd.conf
systemctl restart lrbd.service
systemctl status -l lrbd.service
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $IGWNODE
}

function igw_info {
  #
  # peek at igw information on the igw node
  #
  local TESTSCRIPT=/tmp/igw_info.sh
  local IGWNODE=$(_first_x_node igw)
  cat << 'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "igw info script running as $(whoami) on $(hostname --fqdn)"
rpm -q lrbd || true
lrbd --output || true
ls -lR /sys/kernel/config/target/ || true
ss --tcp --numeric state listening
echo "See 3260 there?"
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $IGWNODE
}

function iscsi_mount_and_sanity_test {
  #
  # run iscsi mount test script on the client node
  # mounts iscsi in /mnt, touches a file, asserts that it exists
  #
  local TESTSCRIPT=/tmp/iscsi_test.sh
  local CLIENTNODE=$(_client_node)
  local IGWNODE=$(_first_x_node igw)
  cat << EOF > $TESTSCRIPT
set -e
trap 'echo "Result: NOT_OK"' ERR
for delay in 60 60 60 60 ; do
    sudo zypper --non-interactive --gpg-auto-import-keys refresh && break
    sleep $delay
done
set -x
zypper --non-interactive install --no-recommends open-iscsi multipath-tools
systemctl start iscsid.service
sleep 5
systemctl status -l iscsid.service
iscsiadm -m discovery -t st -p $IGWNODE
iscsiadm -m node -L all
systemctl start multipathd.service
sleep 5
systemctl status -l multipathd.service
ls -lR /dev/mapper
ls -l /dev/disk/by-path
ls -l /dev/disk/by-*id
multipath -ll
mkfs -t xfs /dev/dm-0
test -d /mnt
mount /dev/dm-0 /mnt
df -h /mnt
touch /mnt/bubba
test -f /mnt/bubba
umount /mnt
echo "Result: OK"
EOF
  # FIXME: assert script not running on the iSCSI gateway node
  _run_test_script_on_node $TESTSCRIPT $CLIENTNODE
}

function validate_rgw_cert_perm {
    local TESTSCRIPT=/tmp/test_rados_put.sh
    local RGWNODE=$(_first_x_node rgw-ssl)
    cat << 'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
RGW_PEM=/etc/ceph/rgw.pem
test -f "$RGW_PEM"
test "$(stat -c'%U' $RGW_PEM)" == "ceph"
test "$(stat -c'%G' $RGW_PEM)" == "ceph"
test "$(stat -c'%a' $RGW_PEM)" -eq 600
echo "Result: OK"
EOF
    _run_test_script_on_node $TESTSCRIPT $RGWNODE
}

function test_systemd_ceph_osd_target_wants {
  #
  # see bsc#1051598 in which ceph-disk was omitting --runtime when it enabled
  # ceph-osd@$ID.service units
  #
  local TESTSCRIPT=/tmp/test_systemd_ceph_osd_target_wants.sh
  local STORAGENODE=$(_first_x_node storage)
  cat << 'EOF' > $TESTSCRIPT
set -x
CEPH_OSD_WANTS="/systemd/system/ceph-osd.target.wants"
ETC_CEPH_OSD_WANTS="/etc$CEPH_OSD_WANTS"
RUN_CEPH_OSD_WANTS="/run$CEPH_OSD_WANTS"
ls -l $ETC_CEPH_OSD_WANTS
ls -l $RUN_CEPH_OSD_WANTS
set -e
trap 'echo "Result: NOT_OK"' ERR
echo "Asserting that there is no directory $ETC_CEPH_OSD_WANTS"
test -d "$ETC_CEPH_OSD_WANTS" && false
echo "Asserting that $RUN_CEPH_OSD_WANTS exists, is a directory, and is not empty"
test -d "$RUN_CEPH_OSD_WANTS"
test -n "$(ls --almost-all $RUN_CEPH_OSD_WANTS)"
echo "Result: OK"
EOF
    _run_test_script_on_node $TESTSCRIPT $STORAGENODE
}

function configure_all_OSDs_to_filestore {
	salt-run proposal.populate format=filestore name=filestore 
	chown salt:salt /srv/pillar/ceph/proposals/policy.cfg
	sed -i 's/profile-default/profile-filestore/g' /srv/pillar/ceph/proposals/policy.cfg
}

function verify_OSD_type {
    # checking with 'ceph osd metadata' command
    # 1st input argument: type 'filestore' or 'bluestore'
    # 2nd input argument: OSD ID 
    osd_type=$(ceph osd metadata $2 -f json-pretty | jq '.osd_objectstore')
    if [[ $osd_type != \"$1\" ]]
        then 
        echo "Error: Object store type is not $1 for OSD.ID : $2"
        exit 1
    else
        echo OSD.${2} $osd_type
    fi
}

function check_OSD_type {  
    # expecting as argument 'filestore' or 'bluestore' 
    for i in $(ceph osd ls);do verify_OSD_type $1 $i;done
}

function migrate_to_bluestore {
	salt-run state.orch ceph.migrate.policy
	sed -i 's/profile-filestore/migrated-profile-filestore/g' /srv/pillar/ceph/proposals/policy.cfg
	salt-run disengage.safety
	salt-run state.orch ceph.migrate.osds
}

function disable_restart_in_stage_0 {
	cp /srv/salt/ceph/stage/prep/master/default.sls /srv/salt/ceph/stage/prep/master/default-orig.sls 
	cp /srv/salt/ceph/stage/prep/master/default-update-no-reboot.sls /srv/salt/ceph/stage/prep/master/default.sls 
	cp /srv/salt/ceph/stage/prep/minion/default.sls /srv/salt/ceph/stage/prep/minion/default-orig.sls 
	cp /srv/salt/ceph/stage/prep/minion/default-update-no-reboot.sls /srv/salt/ceph/stage/prep/minion/default.sls
}

