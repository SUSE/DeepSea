  
{% set master = salt['master.minion']() %}

remove packages:
  salt.state:
    - tgt: '{{ master }}'
    - sls: ceph.packages.remove
    - failhard: True

