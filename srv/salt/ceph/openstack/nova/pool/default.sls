
nova pool:
  cmd.run:
    - name: "ceph osd pool create nova 128"
    - unless: "ceph osd pool ls | grep -q nova$"
    - fire_event: True

