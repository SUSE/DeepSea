{% if (salt.saltutil.runner('select.minions', cluster='ceph', roles='prometheus') != []) %}
restarting prometheus:
  salt.state:
    - tgt: 'I@roles:prometheus and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.restart
    - failhard: True
{% else %}
restarting prometheus:
  test.nop
{% endif %}
