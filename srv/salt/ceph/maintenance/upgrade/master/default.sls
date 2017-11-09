{% set timeout=salt['pillar.get']('minions_ready_timeout', 30) %}
{% if salt.saltutil.runner('minions.ready', timeout=timeout) and salt['saltutil.runner']('upgrade.check') and salt['saltutil.runner']('validate.setup') %}

{% set notice = salt['saltutil.runner']('advise.salt_upgrade') %}
  
sync all:
  salt.state:
    - tgt: '*'
    - sls: ceph.sync
    - failhard: True

set sortbitwise flag: 
  salt.state:
    - sls: ceph.setosdflags.sortbitwise
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

# May generate an unpack error which is safe to ignore
update deepsea and master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.updates.master

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

{% else %}

validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

{% endif %}
