#
# This file is part of the DeepSea integration test suite
#

function rgw_demo_users {
  local RGWSLS=/srv/pillar/ceph/rgw.sls
  cat << EOF >> $RGWSLS
rgw_configurations:
  rgw:
    users:
      - { uid: "demo", name: "Demo", email: "demo@demo.nil" }
      - { uid: "demo1", name: "Demo1", email: "demo1@demo.nil" }
EOF
  cat $RGWSLS
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
radosgw-admin user list
radosgw-admin user info --uid=demo
radosgw-admin user info --uid=demo1
radosgw-admin bucket list
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
zypper --non-interactive --no-gpg-checks refresh
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

