

include:
  - .{{ salt['pillar.get']('ceph_obliterate', 'default') }}
