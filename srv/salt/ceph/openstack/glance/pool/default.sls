{% set prefix = pillar['openstack_prefix'] + "-" if 'openstack_prefix' in pillar else "" %}
{{ prefix }}glance pool:
  cmd.run:
    - name: "ceph osd pool create {{ prefix }}cloud-images 128"
    - unless: "ceph osd pool ls | grep -q ^{{ prefix }}cloud-images$'"
    - fire_event: True

{{ prefix }}glance pool enable application:
  cmd.run:
    - name: "ceph osd pool application enable {{ prefix }}cloud-images rbd || :"

