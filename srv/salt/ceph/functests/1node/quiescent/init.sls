
{% set node = salt.saltutil.runner('select.one_minion', cluster='ceph', roles='storage') %}

{{ node }}:
  test.nop

check active+clean:
  salt.state:
    - tgt: {{ node }}
    - tgt_type: compound
    - sls: ceph.tests.quiescent

check not active+clean:
  salt.state:
    - tgt: {{ node }}
    - tgt_type: compound
    - sls: ceph.tests.quiescent.timeout
