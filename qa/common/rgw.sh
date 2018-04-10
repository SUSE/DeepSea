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
    set +x
    for delay in 60 60 60 60 ; do
        sudo zypper --non-interactive --gpg-auto-import-keys refresh && break
        sleep $delay
    done
    set -x
    zypper --non-interactive install --no-recommends curl libxml2-tools
    RGWNODE=$(salt --no-color -C "I@roles:rgw" test.ping | grep -o -P '^\S+(?=:)' | head -1)
    RGWXMLOUT=/tmp/rgw_test.xml
    curl $RGWNODE > $RGWXMLOUT
    test -f $RGWXMLOUT
    xmllint $RGWXMLOUT
    grep anonymous $RGWXMLOUT
    rm -f $RGWXMLOUT
}


function rgw_curl_test_ssl {
    set +x
    for delay in 60 60 60 60 ; do
        sudo zypper --non-interactive --gpg-auto-import-keys refresh && break
        sleep $delay
    done
    set -x
    zypper --non-interactive install --no-recommends curl libxml2-tools
    RGWNODE=$(salt --no-color -C "I@roles:rgw" test.ping | grep -o -P '^\S+(?=:)' | head -1)
    RGWXMLOUT=/tmp/rgw_test.xml
    curl -k https://$RGWNODE > $RGWXMLOUT
    test -f $RGWXMLOUT
    xmllint $RGWXMLOUT
    grep anonymous $RGWXMLOUT
    rm -f $RGWXMLOUT
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
