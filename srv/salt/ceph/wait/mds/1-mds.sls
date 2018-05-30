wait for mds cluster size 1:
 module.run:
   - name: wait.until_mds
   - kwargs:
       'status': "up:active"
       'mds_count': 1
   - fire_event: True
   - failhard: True
