

push proposals:
  salt.runner:
    - name: push.proposal


ceph_conf refresh_pillar:
  salt.state:
    - tgt: '*'
    - sls: ceph.refresh

post configuration:
  salt.runner:
    - name: configure.cluster

refresh_pillar:
  salt.state:
    - tgt: '*'
    - sls: ceph.refresh



