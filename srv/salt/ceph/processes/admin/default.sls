wait for admin processes:
  module.run:
    - name: cephprocesses.wait
    - kwargs:
        'roles':
          - admin
    - fire_event: True
    - failhard: True
