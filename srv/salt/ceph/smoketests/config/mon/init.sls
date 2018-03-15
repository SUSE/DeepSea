
change ceph.conf:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.tests.config_mon
    - failhard: True

create ceph.conf:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.configuration.create
    - failhard: True

apply configuration:
  salt.state:
    - tgt: 'I@roles:mon'
    - tgt_type: compound
    - sls: ceph.configuration
    - failhard: True

restart mons:
  salt.state:
    - tgt: 'I@roles:mon'
    - tgt_type: compound
    - sls: ceph.mon.restart.force
    - failhard: True

check change:
  salt.state:
    - tgt: 'I@roles:mon'
    - tgt_type: compound
    - sls: ceph.tests.config_mon.check
    - failhard: True

restore ceph.conf:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.tests.config_mon.restore

recreate ceph.conf:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.configuration.create
    - failhard: True

restore configuration:
  salt.state:
    - tgt: 'I@roles:mon'
    - tgt_type: compound
    - sls: ceph.configuration

reset mons:
  salt.state:
    - tgt: 'I@roles:mon'
    - tgt_type: compound
    - sls: ceph.mon.restart.force

