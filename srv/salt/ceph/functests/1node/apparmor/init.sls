{% set master = salt['master.minion']() %}

enforce apparmor profiles:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.apparmor.default-enforce
    - failhard: True

make sure ceph cluster is healthy:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.wait
    - failhard: True
