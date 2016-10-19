{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw', host=True) %}

wait for {{ host }}:
  module.run:
   - name: wait.out
   - kwargs:
       'status': "HEALTH_ERR"
   - fire_event: True
   - failhard: True
         
restart {{ host }}:
  cmd.run:
    - name: "systemctl restart ceph-radosgw@rgw.{{ host }}.service"
    - fire_event: True

{% endfor %}
