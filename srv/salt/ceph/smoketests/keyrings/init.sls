
{% set master = salt['master.minion']() %}

check keyrings:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.tests.keyrings

