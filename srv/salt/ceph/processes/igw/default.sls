wait for igw processes:
  module.run:
    - name: cephprocesses.wait
    - kwargs:
        'roles': 
          - igw
    - fire_event: True
    - failhard: True
