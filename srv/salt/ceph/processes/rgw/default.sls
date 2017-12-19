wait for rgw processes:
  module.run:
    - name: cephprocesses.wait
    - kwargs:
        'roles': 
          - rgw
    - fire_event: True
    - failhard: True
