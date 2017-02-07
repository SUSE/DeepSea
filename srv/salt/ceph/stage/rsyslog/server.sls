{% for host in salt.saltutil.runner('select.minions', roles='rsyslog', host=False) %}
iperf_server_start {{ loop }}:
  salt.state:
    - tgt: {{ host }}
    - sls:
      - ceph.rsyslog.server
{% endfor %}
