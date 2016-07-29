
prepare:
  salt.state:
    - tgt: 'admin*'
    - sls: ceph
