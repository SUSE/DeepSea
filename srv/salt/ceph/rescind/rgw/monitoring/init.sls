

include:
  - .{{ salt['pillar.get']('rescind_rgw_monitoring', 'default') }}
