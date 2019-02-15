reload api:
  cmd.run:
    - name: "systemctl reload rbd-target-api"
    - fire_event: True

reload gateway:
  cmd.run:
    - name: "systemctl reload rbd-target-gw"
    - fire_event: True

