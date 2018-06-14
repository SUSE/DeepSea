
glance pool:
  cmd.run:
    - name: "ceph osd pool create glance 128"
    - unless: "ceph osd pool ls | grep -q glance$"
    - fire_event: True

{{ prefix }}glance pool enable application:
  cmd.run:
    - name: "ceph osd pool application enable {{ prefix }}images rbd || :"

