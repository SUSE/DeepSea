
include:
  - .{{ salt['pillar.get']('osd_takeover', 'default') }}
