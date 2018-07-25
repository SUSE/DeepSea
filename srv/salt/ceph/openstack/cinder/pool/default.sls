{% set prefix = pillar['openstack_prefix'] + "-" if 'openstack_prefix' in pillar else "" %}
{{ prefix }}cinder pool:
  cmd.run:
    - name: "ceph osd pool create {{ prefix }}cloud-volumes 128"
    - unless: "ceph osd pool ls | grep -q '^{{ prefix }}cloud-volumes$'"
    - fire_event: True

{{ prefix }}cinder pool enable application:
  cmd.run:
    - name: "ceph osd pool application enable {{ prefix }}cloud-volumes rbd || :"

