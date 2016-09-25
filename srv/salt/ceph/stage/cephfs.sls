
cephfs pools:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.mds.pools

cephfs auth:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.mds.keyrings

cephfs keyring:
  salt.state:
    - tgt: "I@roles:mds and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.mds.keyring

cephfs:
  salt.state:
    - tgt: "I@roles:mds and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.mds

