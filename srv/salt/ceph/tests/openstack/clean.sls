{% set prefix = pillar['openstack_prefix'] + "-" if 'openstack_prefix' in pillar else "" %}

{% for user in ['cinder', 'cinder-backup', 'glance'] %}
remove client.{{ prefix }}{{ user }}:
  cmd.run:
    - name: "ceph auth rm client.{{ prefix }}{{ user }}"
    - onlyif: "ceph auth get client.{{ prefix }}{{ user }}" 
{% endfor %}

enable pool deletion:
  cmd.run:
    - name: "ceph tell mon.* injectargs --mon-allow-pool-delete=true"

{% for pool in ['cloud-images', 'cloud-volumes', 'cloud-backups', 'cloud-vms'] %}
remove {{ prefix }}{{ pool }}:
  cmd.run:
    - name: "ceph osd pool rm {{ prefix }}{{ pool }} {{ prefix }}{{ pool }} --yes-i-really-really-mean-it"
    - onlyif: "ceph osd pool ls | grep -q '^{{ prefix }}{{ pool }}$'"
{% endfor %}

disable pool deletion:
  cmd.run:
    - name: "ceph tell mon.* injectargs --mon-allow-pool-delete=false"

