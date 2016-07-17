

include:
  - .{{ salt['pillar.get']('configure_method', 'default') }}
