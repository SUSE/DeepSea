
begin:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.begin_prep

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

{% if salt.saltutil.runner('select.minions', cluster='ceph') == [] %}

updates:
  salt.state:
    - tgt: '*'
    - sls: ceph.updates

{% elif salt.saltutil.runner('select.minions', cluster='ceph') != [] and salt['pillar.get']('fsid') != None %}

{% for host in salt.saltutil.runner('getnodes.sorted_unique_nodes', cluster='ceph') %}

wait until the cluster is not in a bad state anymore to process {{ host }}:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.wait

updating {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.updates
    - failhard: True

{% endfor %}

{% else %}

prevent empty rendering:
  test.nop:
    - name: skip

{% endif %}

mines:
  salt.state:
    - tgt: '*'
    - sls: ceph.mines

restart:
  salt.state:
    - tgt: '*'
    - sls: ceph.updates.restart

complete:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.complete_prep
