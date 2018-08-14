
include:
  - .{{ salt['pillar.get']('openstack_cinder-backup_key', 'default') }}
