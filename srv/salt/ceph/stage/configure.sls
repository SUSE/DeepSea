
time:
  salt.state:
    - tgt: salt['pillar.get']('master_minion')
    - sls: ceph.event.begin


include:
  - ceph.stage.configure.{{ salt['pillar.get']('configure_method', 'default') }}

