wait:
 module.run:
   - name: wait.until
   - kwargs:
       'status': "HEALTH_OK"
       'timeout': 14400
   - fire_event: True
   - failhard: True
