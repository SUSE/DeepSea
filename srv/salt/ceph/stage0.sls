
prepare:
  salt.state:
    - tgt: '*'
    - sls: ceph
