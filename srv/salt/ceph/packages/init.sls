

include:
  - .{{ salt['pillar.get']('packages_init', 'default') }}
