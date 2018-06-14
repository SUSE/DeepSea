
cinder pool:
  cmd.run:
    - name: "ceph osd pool create cinder 128"
    - unless: "ceph osd pool ls | grep -q cinder$"
    - fire_event: True

{{ prefix }}cinder pool enable application:
  cmd.run:
    - name: "ceph osd pool application enable {{ prefix }}volumes rbd || :"

