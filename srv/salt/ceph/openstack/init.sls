
include:
  - .{{ salt['pillar.get']('openstack_init', 'default') }}
