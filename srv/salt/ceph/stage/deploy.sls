
time:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.time

admin:
  salt.state:
    - tgt: 'I@roles:admin and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.admin

monitors:
  salt.state:
    - tgt: 'I@roles:mon and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.mon

storage:
  salt.state:
    - tgt: 'I@roles:storage and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.osd

pools:
  salt.state:
    - tgt: {{ salt.saltutil.runner('select.one_minion', cluster='ceph', roles='mon')}}
    - sls: ceph.pool
