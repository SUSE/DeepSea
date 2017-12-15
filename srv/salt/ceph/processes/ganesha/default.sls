wait for ganesha processes:
  module.run:
    - name: cephprocesses.wait
    - kwargs:
        'roles':
          - ganesha
    - fire_event: True
    - failhard: True
