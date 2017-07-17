wait:
 module.run:
   - name: wait.just
   - kwargs:
       'delay': 30
       'nohealthcheck': True
   - fire_event: True
   - failhard: True
