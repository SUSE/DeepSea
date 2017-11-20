{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') %}

cephfs pools:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.mds.pools

mds auth:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.mds.auth

mds:
  salt.state:
    - tgt: "I@roles:mds and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.mds

restart mds:
  salt.state:
    - tgt: "I@roles:mds and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.mds.restart

{% endif %}

