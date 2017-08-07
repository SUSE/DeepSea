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
}
