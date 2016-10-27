restart:
  cmd.run:
    - name: "systemctl restart lrbd"
    - fire_event: True
