
setup:
  salt.state:
    - tgt: 'admin*'
    - sls: ceph.configure
