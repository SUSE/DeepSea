configure dashboard rgw access key:
  cmd.run:
    - name: "echo -n $(radosgw-admin user info --uid=admin | jq -r .keys[0].access_key) | ceph dashboard set-rgw-api-access-key -i -"
    - fire_event: True

configure dashboard rgw secret key:
  cmd.run:
    - name: "echo -n $(radosgw-admin user info --uid=admin | jq -r .keys[0].secret_key) | ceph dashboard set-rgw-api-secret-key -i -"
    - fire_event: True

{% set rgw_init = pillar.get('rgw_init', 'default') %}
{% if rgw_init == "default-ssl" %}
configure dashboard rgw port:
  cmd.run:
    - name: "ceph dashboard set-rgw-api-port {{ pillar.get('rgw_frontend_ssl_port', 443) }}"
    - fire_event: True
{% else %}
configure dashboard rgw port:
  cmd.run:
    - name: "ceph dashboard set-rgw-api-port {{ pillar.get('rgw_frontend_port', 80) }}"
    - fire_event: True
{% endif %}

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
