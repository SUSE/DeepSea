

include:
  - .{{ salt['pillar.get']('admin_method', 'default') }}
