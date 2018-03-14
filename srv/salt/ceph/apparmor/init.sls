
include:
  - .{{ salt['pillar.get']('apparmor_init', 'default') }}
