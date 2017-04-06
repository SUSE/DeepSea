
begin:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.begin_prep

mines:
  salt.state:
    - tgt: '*'
    - sls: ceph.mines

sync:
  salt.state:
    - tgt: '*'
    - sls: ceph.sync

repo:
  salt.state:
    - tgt: '*'
    - sls: ceph.repo

common packages:
  salt.state:
    - tgt: '*'
    - sls: ceph.packages.common

{% if salt['saltutil.runner']('cephprocesses.check', roles=['mon']) == True %}

{% for host in salt.saltutil.runner('orderednodes.unique', cluster='ceph') %}

wait until the cluster has recovered before processing {{ host }}:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.wait
    - failhard: True

check if all processes are still running after processing {{ host }}:
  salt.state:
    - tgt: '*'
    - sls: ceph.cephprocesses
    - failhard: True

# After the last item in the iteration was processed the reactor 
# still sets ceph osd set noout. So setting this after is still necessary.
unset noout after processing {{ host }}:
  salt.state:
    - sls: ceph.noout.unset
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

updating {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.updates
    - failhard: True

restart {{ host }} if updates require:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.updates.restart
    - failhard: True

{% endfor %}

# After the last item in the iteration was processed the reactor 
# still sets ceph osd set noout. So setting this after is still necessary.
unset noout after processing all hosts: 
  salt.state:
    - sls: ceph.noout.unset
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

# Here needs to be 100% definitive check that the cluster is not up yet.
# the parent if conditional can be False if one of the mons is down.
# but even if all are down, this is no indication of rebooting/updateing
# all nodes at once
{% else %}

updates:
  salt.state:
    - tgt: '*'
    - sls: ceph.updates

{% endif %}

complete:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.complete_prep

restart:
  salt.state:
    - tgt: '*'
    - sls: ceph.updates.restart
