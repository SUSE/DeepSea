configure dashboard rgw access key:
  cmd.run:
    - name: "ceph dashboard set-rgw-api-access-key $(radosgw-admin user info --uid=admin | jq -r .keys[0].access_key)"
    - fire_event: True

configure dashboard rgw secret key:
  cmd.run:
    - name: "ceph dashboard set-rgw-api-secret-key $(radosgw-admin user info --uid=admin | jq -r .keys[0].secret_key)"
    - fire_event: True

configure dashboard rgw api user id:
  cmd.run:
    - name: "ceph dashboard set-rgw-api-user-id admin"
    - fire_event: True
