
include:
  - .{{ salt['pillar.get']('openstack_cinder_pool', 'default') }}
