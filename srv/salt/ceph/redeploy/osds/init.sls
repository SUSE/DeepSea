

include:
  - .{{ salt['pillar.get']('redeploy_osds', 'default') }}

