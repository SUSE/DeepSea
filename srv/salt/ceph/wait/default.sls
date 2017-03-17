wait:
 module.run:
   - name: wait.out
   - kwargs:
       'status': "HEALTH_ERR"
   - fire_event: True

cephserives:
  module.run:
    - name: cephprocesses.wait
    - fire_event: True

