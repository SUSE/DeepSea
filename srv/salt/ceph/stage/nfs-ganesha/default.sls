
ganesha setup:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
  