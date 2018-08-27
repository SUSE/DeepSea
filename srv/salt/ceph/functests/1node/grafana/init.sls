{% set master = salt['pillar.get']('master_minion') %}

make sure grafana state is applied:
  salt.state:
    - tgt: '{{ master }}'
    - tgt_type: compound
    - sls: ceph.monitoring.grafana
    - failhard: True

make sure grafana is running:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.tests.grafana.running

