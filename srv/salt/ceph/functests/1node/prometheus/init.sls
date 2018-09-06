{% set master = salt['pillar.get']('master_minion') %}

make sure prometheus state is applied:
  salt.state:
    - tgt: '{{ master }}'
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus
    - failhard: True

make sure prometheus is running:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.tests.prometheus.running

