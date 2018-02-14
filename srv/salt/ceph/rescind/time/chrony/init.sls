
include:
  - .{{ salt['pillar.get']('rescind_time_chrony', 'default') }}
