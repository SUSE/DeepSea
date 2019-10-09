include:
  - .{{ salt['pillar.get']('wait_until_all_osds_in', 'default') }}

