
begin:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.begin_prep
    - require:
      - salt: ready

sync:
  salt.state:
    - tgt: '*'
    - sls: ceph.sync
    - require:
      - salt: begin

mine_functions:
  salt.state:
    - tgt: '*'
    - sls: ceph.mine_functions
    - require:
      - salt: sync

repo:
  salt.state:
    - tgt: '*'
    - sls: ceph.repo
    - require:
      - salt: mine_functions

updates:
  salt.state:
    - tgt: '*'
    - sls: ceph.updates
    - require:
      - salt: repo

complete:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.complete_prep
    - require:
      - salt: updates

