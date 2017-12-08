

include:
  - .{{ salt['pillar.get']('osd_restart_method_lax', 'default') }}

