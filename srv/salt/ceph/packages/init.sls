

include:
  - .{{ salt['pillar.get']('packages_method', 'default') }}
