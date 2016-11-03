{% for host in salt.saltutil.runner('select.minions', cluster='ceph', host=False) %}
iperf_server_start {{ loop }}:
  salt.state:
    - tgt: {{ host }}
    - sls:
      - ceph.iperf
{% endfor %}

{% for testlist in salt.saltutil.runner('nettest.minion_link_ipv4', cluster='ceph') %}
{% set minion = testlist[0] %}
{% set addr = testlist[1] %}
iperf3 {{ loop }}:
  salt.function:
    - tgt: {{ minion }}
    - name: cmd.run
    - arg :
      - 'iperf3 -c {{ addr }} -f m -t 10 -P 1'
{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', host=False) %}
iperf_server_end {{ loop }}:
  salt.state:
    - tgt: {{ host }}
    - sls:
      - ceph.iperf.remove
{% endfor %}
