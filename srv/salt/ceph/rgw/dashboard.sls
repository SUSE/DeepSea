configure dashboard rgw access key:
  cmd.run:
    - name: "ceph dashboard set-rgw-api-access-key $(radosgw-admin user info --uid=admin | jq -r .keys[0].access_key)"
    - fire_event: True

configure dashboard rgw secret key:
  cmd.run:
    - name: "ceph dashboard set-rgw-api-secret-key $(radosgw-admin user info --uid=admin | jq -r .keys[0].secret_key)"
    - fire_event: True

configure dashboard rgw port:
  cmd.run:
    - name: "ceph dashboard set-rgw-api-port {{ pillar.get('rgw_frontend_port', 80) }}"
    - fire_event: True

{% set rgw_minions = salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw') %}
{% if not rgw_minions %}
{% set rgw_minions = salt.saltutil.runner('select.minions', cluster='ceph', rgw_configurations='*') %}
{% endif %}

configure dashboard rgw host:
  cmd.run:
    - name: "ceph dashboard set-rgw-api-host {{ rgw_minions[0] }}"
    - fire_event: True

configure dashboard rgw api user id:
  cmd.run:
    - name: "ceph dashboard set-rgw-api-user-id admin"
    - fire_event: True
