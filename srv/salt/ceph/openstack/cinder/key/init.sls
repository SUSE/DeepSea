
include:
  - .{{ salt['pillar.get']('openstack_cinder_key', 'default') }}
