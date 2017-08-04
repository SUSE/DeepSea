sync:
  salt.state:
    - tgt: '{{ salt['pillar.get']('ceph_tgt') }}'
    - sls: ceph.sync

repo:
  salt.state:
    - tgt: '{{ salt['pillar.get']('ceph_tgt') }}'
    - sls: ceph.repo

common packages:
  salt.state:
    - tgt: '{{ salt['pillar.get']('ceph_tgt') }}'
    - sls: ceph.packages.common

mines:
  salt.state:
    - tgt: '{{ salt['pillar.get']('ceph_tgt') }}'
    - sls: ceph.mines


