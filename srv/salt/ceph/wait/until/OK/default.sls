wait:
 module.run:
   - name: wait.until
   - kwargs:
       'status': "HEALTH_OK"
       'timeout': 300
   - fire_event: True
   - failhard: True
