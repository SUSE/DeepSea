{% for host in salt.saltutil.runner('select.minions', cluster='ceph', host=True) %}
iperf_server_start {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - sls: ceph.iperf
{% endfor %}

{% for host_addr in salt.saltutil.runner('nettest.minion_link_ipv4', cluster='ceph', host=True) %}
{% set host = host_addr[0] %}
{% set addr = host_addr[1] %}
iperf3 {{ host_addr }}:
  salt.function:
    - tgt: {{ host }}
    - name: cmd.run
    - arg :
      - 'iperf3 -c {{ addr }} -f m -t 10 -P 1'
{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', host=True) %}
iperf_server_end {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - sls: ceph.iperf.remove
{% endfor %}
