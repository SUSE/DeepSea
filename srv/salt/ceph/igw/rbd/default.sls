
create rbd pool:
  cmd.run:
    - name: "ceph osd pool create rbd 128"
    - unless: "ceph osd pool ls | grep -q rbd$"
    - fire_event: True

