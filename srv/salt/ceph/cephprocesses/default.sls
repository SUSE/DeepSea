wait processes:
  module.run:
    - name: cephprocesses.check
    - fire_event: True
    - failhard: True
