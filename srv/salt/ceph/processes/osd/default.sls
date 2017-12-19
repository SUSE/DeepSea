wait for osd processes:
  module.run:
    - name: cephprocesses.wait
    - kwargs:
        'roles': 
          - storage
    - fire_event: True
    - failhard: True
