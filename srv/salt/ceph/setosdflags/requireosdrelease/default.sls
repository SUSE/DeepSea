osd flags require osd release luminous:
  cmd.run:
    - name: "ceph osd require-osd-release luminous"
    - fire_event: True
