

include:
  - .{{ salt['pillar.get']('ceph_obliterate_unlock', 'default') }}
