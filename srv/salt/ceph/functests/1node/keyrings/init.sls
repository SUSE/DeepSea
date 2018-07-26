
check keyrings:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.tests.keyrings

