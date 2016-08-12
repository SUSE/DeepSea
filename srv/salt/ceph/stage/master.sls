
packages:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.packages

prepare master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.prep.master


#openattic:
#  salt.state:
#    - tgt: {{ salt['pillar.get']('master_minion') }}
#    - sls: ceph.openattic

{% set marker = salt.saltutil.runner('filequeue.add', queue='master', name='complete') %}

include:
  - .prep

{% set marker = salt.saltutil.runner('filequeue.remove', queue='master', name='begin') %}
