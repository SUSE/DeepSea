wait for {{ grains['host'] }}:
  module.run:
   - name: wait.out
   - kwargs:
       'status': "HEALTH_ERR"
   - fire_event: True
   - failhard: True

restart @{{ grains['host'] }}:
  cmd.run:
    - name: "systemctl restart ceph-mon@{{ grains['host'] }}.service"
    - fire_event: True

