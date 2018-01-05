
include:
  - .{{ salt['pillar.get']('openstack_nova', 'default') }}
