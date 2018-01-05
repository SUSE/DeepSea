
include:
  - .{{ salt['pillar.get']('openstack_glance_pool', 'default') }}
