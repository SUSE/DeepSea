wait for openattic processes:
  module.run:
    - name: cephprocesses.wait
    - kwargs:
        'roles': 
          - openattic
    - fire_event: True
    - failhard: True
