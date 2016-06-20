
setup:
  salt.state:
    - tgt: 'admin*'
    - sls: ceph.setup

refresh_pillar:
  salt.state:
    - tgt: '*'
    - sls: ceph.refresh
