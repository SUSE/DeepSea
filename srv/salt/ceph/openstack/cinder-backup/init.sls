
include:
  - .{{ salt['pillar.get']('openstack_cinder-backup', 'default') }}
