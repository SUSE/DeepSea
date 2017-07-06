wait:
 module.run:
   - name: wait.until
   - kwargs:
       'status': "HEALTH_OK"
       'timeout': 7200
   - fire_event: True
   - failhard: True
