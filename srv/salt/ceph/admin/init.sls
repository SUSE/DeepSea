

include:
  - .{{ salt['pillar.get']('admin_init', 'default') }}
