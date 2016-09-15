

include:
  - ceph.stage.configure.{{ salt['pillar.get']('configure_method', 'default') }}

