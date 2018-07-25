Apply mgr tuned states:
  salt.state:
    - tgt: 'I@roles:mgr and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.tuned.mgr

Apply mon tuned states:
  salt.state:
    - tgt: 'I@roles:mon and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.tuned.mon

Apply osd tuned states:
  salt.state:
    - tgt: 'I@roles:storage and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.tuned.osd

Check tuned for ses roles:
  salt.state:
    - tgt: "I@roles:storage or I@roles:mon or I@roles:mgr"
    - tgt_type: compound
    - sls: ceph.tests.tuned
