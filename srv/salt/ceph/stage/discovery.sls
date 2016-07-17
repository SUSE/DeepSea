
include:
  - ceph.setup.{{ salt['pillar.get']('discovery_method', 'default') }}

refresh_pillar:
  salt.state:
    - tgt: '*'
    - sls: ceph.refresh
