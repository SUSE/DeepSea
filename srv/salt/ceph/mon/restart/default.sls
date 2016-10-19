{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mon', host=True) %}

wait for {{ host }}:
  module.run:
   - name: wait.out
   - kwargs:
       'status': "HEALTH_ERR"
   - fire_event: True
   - failhard: True

restart {{ host }}:
  cmd.run:
    - name: "systemctl restart ceph-mon@{{ host }}.service"
    - fire_event: True

{% endfor %}
