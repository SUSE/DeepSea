{% if salt['saltutil.runner']('validate.setup') == False %}

validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

{% endif %}

update deepsea:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.updates.self
  
sync master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.sync

upgrading:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.upgrade
    - failhard: True

restart master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.updates.restart

ready:
  salt.runner:
    - name: minions.ready
    - timeout: {{ salt['pillar.get']('ready_timeout', 300) }}

