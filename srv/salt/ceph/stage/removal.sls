
update mines:
  salt.function:
    - name: mine.update
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound


remove mon:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.remove.mon

empty osds:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.remove.storage


rescind roles:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.rescind

