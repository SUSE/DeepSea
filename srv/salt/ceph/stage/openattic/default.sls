
openattic nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='openattic') %}

openattic auth:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.openattic.auth

openattic:
  salt.state:
    - tgt: "I@roles:openattic"
    - tgt_type: compound
    - sls: ceph.openattic

openattic keyring:
  salt.state:
    - tgt: "I@roles:openattic"
    - tgt_type: compound
    - sls: ceph.openattic.keyring

openattic oaconfig:
  salt.state:
    - tgt: "I@roles:openattic"
    - tgt_type: compound
    - sls: ceph.openattic.oaconfig

{% endif %}
