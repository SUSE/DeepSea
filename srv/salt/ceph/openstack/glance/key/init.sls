
include:
  - .{{ salt['pillar.get']('openstack_glance_key', 'default') }}
