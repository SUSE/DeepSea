
include:
  - .{{ salt['pillar.get']('openstack_cinder-backup_auth', 'default') }}
