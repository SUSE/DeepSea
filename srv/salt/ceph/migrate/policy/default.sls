
migrate policy.cfg and profiles:
  salt.runner:
    - name: push.convert

refresh pillar:
  salt.state:
    - tgt: '*'
    - sls: ceph.refresh

