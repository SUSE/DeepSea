

include:
  - .{{ salt['pillar.get']('packages_remove', 'default') }}
