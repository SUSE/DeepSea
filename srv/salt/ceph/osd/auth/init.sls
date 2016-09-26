

include:
  - .{{ salt['pillar.get']('osd_auth', 'default') }}

