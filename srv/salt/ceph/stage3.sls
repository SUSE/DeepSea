
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
