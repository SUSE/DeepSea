restart api:
  cmd.run:
    - name: "systemctl restart rbd-target-api"
    - fire_event: True
