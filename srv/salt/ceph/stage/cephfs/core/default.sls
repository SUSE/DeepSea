
{% set master = salt['master.minion']() %}

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') %}

cephfs pools:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.mds.pools

mds auth:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.mds.auth

mds:
  salt.state:
    - tgt: "I@roles:mds and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.mds

{% endif %}

