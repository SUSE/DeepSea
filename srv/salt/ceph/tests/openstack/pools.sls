{% set prefix = pillar['openstack_prefix'] + "-" if 'openstack_prefix' in pillar else "" %}

{% for pool in ['cloud-images', 'cloud-volumes', 'cloud-backups', 'cloud-vms'] %}
verify {{ prefix }}{{ pool }} exists:
  cmd.run:
    - name: "rados lspools | grep '^{{ prefix }}{{ pool }}$' >/dev/null"
{% endfor %}

