restart:
  cmd.run:
    - name: "systemctl reload lrbd"
    - fire_event: True
