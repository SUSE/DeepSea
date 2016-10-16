
# No pools are created by default

wait:
  module.run:
    - name: wait.out
    - kwargs:
        'status': "HEALTH_ERR"
    - fire_event: True

demo image:
  cmd.run:
    - name: "rbd -p rbd create demo --size=1024"
    - unless: "rbd -p rbd ls | grep -q demo$"
    - fire_event: True

