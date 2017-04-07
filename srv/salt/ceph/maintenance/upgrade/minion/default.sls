# preflight

ready:
  salt.runner:
    - name: minions.ready
    - timeout: {{ salt['pillar.get']('ready_timeout', 300) }}

mines:
  salt.state:
    - tgt: '*'
    - sls: ceph.mines

sync:
  salt.state:
    - tgt: '*'
    - sls: ceph.sync

warning_after:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.warning.noout
    - failhard: True

{% for host in salt.saltutil.runner('orderednodes.unique', cluster='ceph') %}

wait until the cluster is not in a bad state anymore to process {{ host }}:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.wait
    - failhard: True

check if services are up after processing {{ host }}:
  salt.state:
    - tgt: "*"
    - sls: ceph.cephprocesses
    - failhard: True

upgrading {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.upgrade
    - failhard: True

rebooting {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.updates.restart
    - fire_event: 'salt/ceph/set/noout'
    - failhard: True

{% endfor %}

# After the last item in the iteration was processed the reactor 
# still sets ceph osd set noout. So setting this after is still necessary.
unset noout after processing all hosts: 
  salt.state:
    - sls: ceph.noout.unset
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

warning_after:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.warning.noout
    - failhard: True

#postflight
