
include:
  - .{{ salt['pillar.get']('osd_restart_parallel_init', 'default') }}

