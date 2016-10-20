{% for host_addr in salt.saltutil.runner('nettest.minion_link_ipv4', cluster='ceph', host=True) %}
{% set host = host_addr[0] %}
{% set addr = host_addr[1] %}
iperf3 {{ host_addr }}:
  salt.function:
    - tgt: {{ host }}
    - name: cmd.run
    - arg :
      - 'ping -c 4 {{ addr }}'
{% endfor %}
