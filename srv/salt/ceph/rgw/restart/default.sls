wait:
  module.run:
   - name: wait.out
   - kwargs:
       'status': "HEALTH_ERR"
   - fire_event: True
         
restart:
  cmd.run:
    - name: "systemctl restart ceph-radosgw@rgw.{{ grains['host'] }}.service"
    - fire_event: True
