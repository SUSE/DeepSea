{% if (salt.saltutil.runner('select.minions', cluster='ceph', roles='grafana') != []) %}
restarting grafana:
  salt.state:
    - tgt: 'I@roles:grafana and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.monitoring.grafana.restart
    - failhard: True
{% else %}
restarting grafana:
  test.nop
{% endif %}
