
prepare master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph

packages:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.packages

#openattic:
#  salt.state:
#    - tgt: {{ salt['pillar.get']('master_minion') }}
#    - sls: ceph.openattic

include:
  - .prep
