
{% set node = salt.saltutil.runner('select.one_minion', cluster='ceph', roles='storage') %}

verify iperf3:
  salt.state:
    - tgt: {{ node }}
    - tgt_type: compound
    - sls: ceph.tests.iperf3

