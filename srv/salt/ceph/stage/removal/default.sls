
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

remove mgr:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.remove.mgr

drain osds:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.remove.storage.drain

terminate ceph osds:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.rescind.storage.terminate

cleanup osds:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.remove.storage

remove ganesha:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.remove.ganesha

rescind roles:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.rescind

remove openattic:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.remove.openattic
