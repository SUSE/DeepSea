
cephfs pools:
  salt.state:
    - tgt: "{{ salt.saltutil.runner('select.one_minion', cluster='ceph', roles='mds') }}"
    - sls: ceph.mds.pools

mds:
  salt.state:
    - tgt: "I@roles:mds and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.mds
    - require:
      - salt: cephfs pools

