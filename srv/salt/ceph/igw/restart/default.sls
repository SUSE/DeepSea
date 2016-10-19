{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='igw', host=True) %}

wait for {{ host }}:
  module.run:
   - name: wait.out
   - kwargs:
       'status': "HEALTH_ERR"
   - fire_event: True
   - failhard: True

restart {{ host }}:
  cmd.run:
    - name: "lrbd"
    - fire_event: True

{% endfor %}
