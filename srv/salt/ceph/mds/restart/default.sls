wait:
  module.run:
   - name: wait.out
   - kwargs:
       'status': "HEALTH_ERR"
   - fire_event: True
   - failhard: True

restart:
  cmd.run:
    - name: "systemctl restart ceph-mds@{{ grains['host'] }}.service"
    - fire_event: True

