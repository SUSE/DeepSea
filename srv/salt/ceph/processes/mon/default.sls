wait for mon processes:
  module.run:
    - name: cephprocesses.wait
    - kwargs:
        'roles': 
          - mon
    - fire_event: True
    - failhard: True
