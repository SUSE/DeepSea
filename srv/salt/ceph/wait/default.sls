wait:
 module.run:
   - name: wait.out
   - kwargs:
       'status': "HEALTH_ERR"
   - fire_event: True
   - failhard: True
