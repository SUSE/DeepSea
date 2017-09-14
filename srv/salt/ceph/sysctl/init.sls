
include:
  - .{{ salt['pillar.get']('sysctl_init', 'default') }}

