
include:
  - .{{ salt['pillar.get']('openstack_glance_auth', 'default') }}
