
include:
  - .{{ salt['pillar.get']('openstack_cinder', 'default') }}
