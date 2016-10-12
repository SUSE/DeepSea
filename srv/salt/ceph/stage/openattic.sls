
openattic auth:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.openattic.auth

openattic:
  salt.state:
    - tgt: "I@roles:master"
    - tgt_type: compound
    - sls: ceph.openattic

openattic keyring:
  salt.state:
    - tgt: "I@roles:master"
    - tgt_type: compound
    - sls: ceph.openattic.keyring

openattic oaconfig:
  salt.state:
    - tgt: "I@roles:master"
    - tgt_type: compound
    - sls: ceph.openattic.oaconfig


