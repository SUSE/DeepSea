

include:
  - .{{ salt['pillar.get']('admin_key', 'default') }}
