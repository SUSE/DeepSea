
include:
  - .{{ salt['pillar.get']('openstack_nova_key', 'default') }}
