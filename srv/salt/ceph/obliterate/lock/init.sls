

include:
  - .{{ salt['pillar.get']('ceph_obliterate_lock', 'default') }}
