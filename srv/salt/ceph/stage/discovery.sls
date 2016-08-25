
ready:
  salt.runner:
    - name: minions.ready

include:
  - ceph.stage.discovery.{{ salt['pillar.get']('discovery_method', 'default') }}

refresh_pillar:
  salt.state:
    - tgt: '*'
    - sls: ceph.refresh
