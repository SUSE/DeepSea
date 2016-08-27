
ready:
  salt.runner:
    - name: minions.ready
    - timeout: {{ salt['pillar.get']('ready_timeout', 300) }}

include:
  - ceph.stage.discovery.{{ salt['pillar.get']('discovery_method', 'default') }}

refresh_pillar:
  salt.state:
    - tgt: '*'
    - sls: ceph.refresh
