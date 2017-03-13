
begin:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.begin_prep

sync:
  salt.state:
    - tgt: '*'
    - sls: ceph.sync

repo:
  salt.state:
    - tgt: '*'
    - sls: ceph.repo

common packages:
  salt.state:
    - tgt: '*'
    - sls: ceph.packages.common

updates:
  salt.state:
    - tgt: '*'
    - sls: ceph.updates

restart:
  salt.state:
    - tgt: '*'
    - sls: ceph.updates.restart

mines:
  salt.state:
    - tgt: '*'
    - sls: ceph.mines

complete:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.complete_prep

