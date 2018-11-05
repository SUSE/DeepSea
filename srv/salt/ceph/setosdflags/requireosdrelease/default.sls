osd flags require osd release nautilus:
  cmd.run:
    - name: "ceph osd require-osd-release nautilus"
    - fire_event: True
