#
# This file is part of the DeepSea integration test suite
#

function rgw_demo_users {
  local RGWSLS=/srv/salt/ceph/rgw/users/users.d/users.yml
  cat << EOF >> $RGWSLS
- { uid: "demo", name: "Demo", email: "demo@demo.nil" }
- { uid: "demo1", name: "Demo1", email: "demo1@demo.nil" }
EOF
  cat $RGWSLS
}

function rgw_user_and_bucket_list {
  #
  # just list rgw users and buckets
  #
  local TESTSCRIPT=/tmp/rgw_user_and_bucket_list.sh
  local RGWNODE=$(_first_x_node rgw)
  cat << EOF > $TESTSCRIPT
set -ex
radosgw-admin user list
radosgw-admin bucket list
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $RGWNODE
}

function rgw_validate_system_user {
  #
  # prove the system user "admin" was really set up
  #
  local TESTSCRIPT=/tmp/rgw_validate_system_user.sh
  local RGWNODE=$(_first_x_node rgw)
  cat << EOF > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
radosgw-admin user info --uid=admin
radosgw-admin user info --uid=admin | grep system | grep -q true
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $RGWNODE
}

function rgw_validate_demo_users {
  #
  # prove the demo users from rgw_demo_users were really set up
  #
  local TESTSCRIPT=/tmp/rgw_validate_demo_users.sh
  local RGWNODE=$(_first_x_node rgw)
  cat << EOF > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
radosgw-admin user info --uid=demo
radosgw-admin user info --uid=demo1
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $RGWNODE
}

function rgw_curl_test {
  local TESTSCRIPT=/tmp/rgw_test.sh
  cat << 'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "rgw curl test running as $(whoami) on $(hostname --fqdn)"
RGWNODE=$(salt --no-color -C "I@roles:rgw" test.ping | grep -o -P '^\S+(?=:)' | head -1)
set +x
for delay in 60 60 60 60 ; do
    sudo zypper --non-interactive --gpg-auto-import-keys refresh && break
    sleep $delay
done
set -x
zypper --non-interactive install --no-recommends curl libxml2-tools
RGWXMLOUT=/tmp/rgw_test.xml
curl $RGWNODE > $RGWXMLOUT
test -f $RGWXMLOUT
xmllint $RGWXMLOUT
grep anonymous $RGWXMLOUT
rm -f $RGWXMLOUT
echo "Result: OK"
EOF
  _run_test_script_on_node $TESTSCRIPT $SALT_MASTER
}


function rgw_curl_test_ssl {
    local TESTSCRIPT=/tmp/rgw_test.sh
    cat << 'EOF' > $TESTSCRIPT
set -ex
trap 'echo "Result: NOT_OK"' ERR
echo "rgw curl test running as $(whoami) on $(hostname --fqdn)"
RGWNODE=$(salt --no-color -C "I@roles:rgw" test.ping | grep -o -P '^\S+(?=:)' | head -1)
set +x
for delay in 60 60 60 60 ; do
    sudo zypper --non-interactive --gpg-auto-import-keys refresh && break
    sleep $delay
done
set -x
zypper --non-interactive install --no-recommends curl libxml2-tools
RGWXMLOUT=/tmp/rgw_test.xml
curl -k https://$RGWNODE > $RGWXMLOUT
test -f $RGWXMLOUT
xmllint $RGWXMLOUT
grep anonymous $RGWXMLOUT
rm -f $RGWXMLOUT
echo "Result: OK"
EOF
    _run_test_script_on_node $TESTSCRIPT $SALT_MASTER
}

function rgw_add_ssl_global {
    local GLOBALYML=/srv/pillar/ceph/stack/global.yml
    cat <<EOF >> $GLOBALYML
rgw_init: default-ssl
rgw_configurations:
  rgw:
    users:
      - { uid: "admin", name: "Admin", email: "admin@demo.nil", system: True }
  # when using only RGW& not ganesha ssl will have all the users of rgw already,
  # but to be consistent we define atleast one user
  rgw-ssl:
    users:
      - { uid: "admin", name: "Admin", email: "admin@demo.nil", system: True }
EOF
    cat $GLOBALYML
}

function rgw_ssl_init {
    local CERTDIR=/srv/salt/ceph/rgw/cert
    mkdir -p $CERTDIR
    pushd $CERTDIR
    openssl req -x509 -nodes -days 1095 -newkey rsa:4096 -keyout rgw.key -out rgw.crt -subj "/C=DE"
    cat rgw.key > rgw.pem && cat rgw.crt >> rgw.pem
    popd
    rgw_add_ssl_global
}

function rgw_configure_2_zones {
    realm=suseqa
    zonegroup=eu
    zone1=eu-east-1
    zone2=eu-east-2
    zone_user=zoneadmin
    rgw1_hostname=$(salt -C 'I@roles:rgw'  network.get_hostname --out txt|awk -F "." '{print $1}'|head -n 1);echo $rgw1_hostname
    rgw2_hostname=$(salt -C 'I@roles:rgw'  network.get_hostname --out txt|awk -F "." '{print $1}'|grep -v $rgw1_hostname);echo $rgw2_hostname
    rgw1_IP=$(salt $rgw1_hostname\* network.ipaddrs --out txt|awk -F "'" '{print $2}'|head -n 1|tr -d ' ')
    [[ -n $rgw1_IP ]] && echo $rgw1_IP || exit 1
    rgw2_IP=$(salt $rgw2_hostname\* network.ipaddrs --out txt|awk -F "'" '{print $2}'|head -n 1|tr -d ' ')
    [[ -n $rgw2_IP ]] && echo $rgw1_IP || exit 1
    SYSTEM_ACCESS_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1)
    SYSTEM_SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1)
    sed -i "/client.rgw.${rgw1_hostname}/a\rgw_zone=$zone1" /etc/ceph/ceph.conf
    sed -i "/client.rgw.${rgw2_hostname}/a\rgw_zone=$zone2" /etc/ceph/ceph.conf
    salt-cp '*' '/etc/ceph/ceph.conf' '/etc/ceph/'
    radosgw-admin realm create --rgw-realm=$realm --default
    radosgw-admin zonegroup delete --rgw-zonegroup=default
    radosgw-admin zone delete --rgw-zone=default 
    radosgw-admin zonegroup create --rgw-zonegroup=$zonegroup --endpoints=http://${rgw1_IP}:80 --master --default
    radosgw-admin zone create --rgw-zonegroup=$zonegroup --rgw-zone=$zone1 \
    --endpoints=http://${rgw1_IP}:80 --access-key=$SYSTEM_ACCESS_KEY --secret=$SYSTEM_SECRET_KEY --master --default
    radosgw-admin user create --uid=$zone_user --display-name="Zone User - primary zone" --access-key=$SYSTEM_ACCESS_KEY --secret=$SYSTEM_SECRET_KEY --system
    radosgw-admin user list --rgw-zone=$zone1
    radosgw-admin period get
    radosgw-admin period update --commit
    salt ${rgw1_hostname}\* cmd.run "systemctl restart ceph-radosgw@rgw.${rgw1_hostname}.service"
    rgw1_service_running=$(salt ${rgw1_hostname}\* service.status ceph-radosgw@rgw.${rgw1_hostname}.service --out txt|awk -F ':' '{print $2}'|tr -d ' ')
    [[ $rgw1_service_running == 'True' ]] && echo "RGW service running."
    radosgw-admin zone create --rgw-zonegroup=$zonegroup --endpoints=http://${rgw2_IP}:80 \
    --rgw-zone=$zone2 --access-key=$SYSTEM_ACCESS_KEY --secret=$SYSTEM_SECRET_KEY
    radosgw-admin period update --commit
    salt ${rgw2_hostname}\* cmd.run "systemctl restart ceph-radosgw@rgw.${rgw2_hostname}.service"
    rgw2_service_running=$(salt ${rgw2_hostname}\* service.status ceph-radosgw@rgw.${rgw2_hostname}.service --out txt|awk -F ':' '{print $2}'|tr -d ' ')
    [[ $rgw2_service_running == 'True' ]] && echo "RGW service running."
    timeout_counter=1
    while sleep 5
    do 
      radosgw-admin sync status|grep syncing && break || echo waiting
      if [[ timeout_counter -gt 20 ]];then echo "Error: Sync TIMEOUT.";exit 1;fi
      ((timeout_counter++))
    done
    radosgw-admin sync status 
    radosgw-admin user list --rgw-zone=$zone2|grep $zone_user # checking if user replicated to secondary zone 
    curl $rgw1_IP|grep anonymous
    curl $rgw2_IP|grep anonymous
}

function rgw_python-booto_rw_test {
    # iterate trough each RGW node and execute python script 
    # argument is rgw user id
    for i in $(salt -C 'I@roles:rgw'  network.get_hostname --out txt|awk -F "." '{print $1}')
    do
        RGW_IP_ADDR=$(salt $i\* network.ipaddrs --out txt|awk -F "'" '{print $2}')
        RGW_TCP_port=$(cat /etc/ceph/ceph.conf|grep -A 5 client.rgw.$i|grep "civetweb port"|grep -oE "[1-9][0-9]+")
        python common/rgw_s3_rw_test.py $RGW_IP_ADDR:$RGW_TCP_port $1
    done
} 

