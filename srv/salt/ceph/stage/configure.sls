

include:
  - ceph.configure.{{ salt['pillar.get']('configure_method', 'default') }}

