{% set prefix = pillar['openstack_prefix'] + "-" if 'openstack_prefix' in pillar else "" %}
{{ prefix }}nova pool:
  cmd.run:
    - name: "ceph osd pool create {{ prefix }}cloud-vms 128"
    - unless: "ceph osd pool ls | grep -q '^{{ prefix }}cloud-vms$'"
    - fire_event: True

{{ prefix }}nova pool enable application:
  cmd.run:
    - name: "ceph osd pool application enable {{ prefix }}cloud-vms rbd || :"

