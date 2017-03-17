
begin:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.begin_prep

mines:
  salt.state:
    - tgt: '*'
    - sls: ceph.mines

sync:
  salt.state:
    - tgt: '*'
    - sls: ceph.sync

repo:
  salt.state:
    - tgt: '*'
    - sls: ceph.repo

common packages:
  salt.state:
    - tgt: '*'
    - sls: ceph.packages.common

{% if salt['saltutil.runner']('cephprocesses.check', roles=['mon']) == True %}

{% for host in salt.saltutil.runner('orderednodes.unique', cluster='ceph') %}

wait until the cluster has recovered before processing {{ host }}:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.wait
    - failhard: True

.include:
- ceph.maintenance.update

{% endfor %}

{% else %}

.include:
- ceph.maintenance.update

{% endif %}


complete:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.complete_prep

