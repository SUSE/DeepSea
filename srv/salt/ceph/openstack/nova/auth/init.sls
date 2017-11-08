
include:
  - .{{ salt['pillar.get']('openstack_nova_auth', 'default') }}
