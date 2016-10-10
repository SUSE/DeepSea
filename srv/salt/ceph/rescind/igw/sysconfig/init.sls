

include:
  - .{{ salt['pillar.get']('rescind_igw_sysconfig', 'default') }}
