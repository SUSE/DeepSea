

include:
  - .{{ salt['pillar.get']('igw_sysconfig', 'default') }}
