wait for mgr processes:
  module.run:
    - name: cephprocesses.wait
    - kwargs:
        'roles': 
          - mgr
    - fire_event: True
    - failhard: True
