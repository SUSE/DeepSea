
include:
  - .{{ salt['pillar.get']('openstack_glance', 'default') }}
