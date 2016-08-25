

include:
  - .{{ salt['pillar.get']('package_method', 'default') }}
