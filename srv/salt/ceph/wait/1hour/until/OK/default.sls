wait:
 module.run:
   - name: wait.until
   - kwargs:
       'status': "HEALTH_OK"
       'timeout': 3600
   - fire_event: True
   - failhard: True
