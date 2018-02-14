
include:
  - .{{ salt['pillar.get']('time_chrony', 'default') }}

