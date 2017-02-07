{% for host in salt.saltutil.runner('select.minions', cluster='ceph', host=False) %}
iperf_server_start {{ loop }}:
  salt.state:
    - tgt: {{ host }}
    - sls:
      - ceph.rsyslog.client
{% endfor %}
