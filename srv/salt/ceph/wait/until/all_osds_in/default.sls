wait for OSDs:
 module.run:
   - name: wait.until_all_osds_in
   - kwargs:
       'timeout': 300
   - fire_event: True
   - failhard: True
