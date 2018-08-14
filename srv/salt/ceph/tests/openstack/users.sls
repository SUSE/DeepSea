{% set prefix = pillar['openstack_prefix'] + "-" if 'openstack_prefix' in pillar else "" %}

{% for user in ['cinder', 'cinder-backup', 'glance'] %}
verify client.{{ prefix }}{{ user }} exists:
  cmd.run:
    - name: "ceph auth get client.{{ prefix }}{{ user }} >/dev/null"
{% endfor %}

