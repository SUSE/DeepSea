
cinder pool:
  cmd.run:
    - name: "ceph osd pool create cinder 128"
    - unless: "ceph osd pool ls | grep -q cinder$"
    - fire_event: True

