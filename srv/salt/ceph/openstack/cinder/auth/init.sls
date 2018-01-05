
include:
  - .{{ salt['pillar.get']('openstack_cinder_auth', 'default') }}
