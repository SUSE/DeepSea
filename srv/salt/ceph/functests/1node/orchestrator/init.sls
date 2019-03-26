{% set master = salt['master.minion']() %}

check orchestrator:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.tests.orchestrator
