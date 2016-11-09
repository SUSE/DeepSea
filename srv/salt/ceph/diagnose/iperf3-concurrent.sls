{% for host in salt.saltutil.runner('select.minions', cluster='ceph', host=False) %}
iperf_server_start {{ loop }}:
  salt.state:
    - tgt: {{ host }}
    - sls:
      - ceph.iperf
      - ceph.iperf.ceph_diagnose_iperf_client_add
{% endfor %}

{% for testlist in salt.saltutil.runner('nettest.minion_link_ipv4_parallel_pair', cluster='ceph') %}
{% set host_list = testlist[0] %}
{% set addr_data = testlist[1] %}
iperf3 {{ loop }}:
  salt.function:
    - tgt: 'L@{{ host_list }}'
    - tgt_type: compound
    - name: cmd.run
    - arg :
      - "/usr/bin/ceph_diagnose_iperf_client.py {{host_list}} {{ addr_data }} -f -t 10 -P 1"
{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', host=False) %}
iperf_server_end {{ loop }}:
  salt.state:
    - tgt: {{ host }}
    - sls:
      - ceph.iperf.remove
      - ceph.iperf.ceph_diagnose_iperf_client_remove
{% endfor %}
