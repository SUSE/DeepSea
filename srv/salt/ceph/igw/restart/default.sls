reload gateway:
  cmd.run:
    - name: "systemctl restart rbd-target-gw"
    - fire_event: True
