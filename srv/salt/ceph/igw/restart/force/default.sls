restart api:
  cmd.run:
    - name: "systemctl restart rbd-target-api"
    - fire_event: True

restart gateway:
  cmd.run:
    - name: "systemctl restart rbd-target-gw"
    - fire_event: True
