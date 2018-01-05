
include:
  - .{{ salt['pillar.get']('openstack_nova_pool', 'default') }}
