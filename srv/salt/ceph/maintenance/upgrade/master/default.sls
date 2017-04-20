{% if salt['saltutil.runner']('validate.setup') == False %}

validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

{% endif %}

{% set notice =  salt['saltutil.runner']('advise.salt_upgrade') %}

# May generate an unpack error which is safe to ignore
update deepsea and master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.updates.self
  
sync master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.sync
    - failhard: True

upgrading:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.upgrade
    - failhard: True

reboot master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.updates.restart


