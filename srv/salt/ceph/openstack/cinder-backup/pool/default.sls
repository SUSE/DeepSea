cinder-backup pool:
  cmd.run:
    - name: "ceph osd pool create backups 128"
    - unless: "ceph osd pool ls | grep -q '^backups$'"
    - fire_event: True

