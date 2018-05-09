  
remove packages:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - sls: ceph.packages.remove
    - failhard: True

