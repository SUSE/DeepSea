wait for mds processes:
  module.run:
    - name: cephprocesses.wait
    - kwargs:
        'roles': 
          - mds
    - fire_event: True
    - failhard: True
