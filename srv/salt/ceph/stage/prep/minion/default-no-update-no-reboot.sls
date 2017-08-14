sync:
  salt.state:
    - tgt: '{{ salt['pillar.get']('ceph_tgt') }}'
    - tgt_type: compound
    - sls: ceph.sync

repo:
  salt.state:
    - tgt: '{{ salt['pillar.get']('ceph_tgt') }}'
    - tgt_type: compound
    - sls: ceph.repo

common packages:
  salt.state:
    - tgt: '{{ salt['pillar.get']('ceph_tgt') }}'
    - tgt_type: compound
    - sls: ceph.packages.common

mines:
  salt.state:
    - tgt: '{{ salt['pillar.get']('ceph_tgt') }}'
    - tgt_type: compound
    - sls: ceph.mines


