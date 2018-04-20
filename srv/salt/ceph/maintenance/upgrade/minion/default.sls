
{% set master = salt['master.minion']() %}

{% set timeout=salt['pillar.get']('minions_ready_timeout', 30) %}
{% if salt.saltutil.runner('minions.ready', timeout=timeout) %}

update salt:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - sls: ceph.updates.salt

mines:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - sls: ceph.mines
    - failhard: True

sync:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - sls: ceph.sync
    - failhard: True

repo:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - sls: ceph.repo
    - failhard: True

common packages:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - sls: ceph.packages.common
    - failhard: True

{% if salt['saltutil.runner']('cephprocesses.mon') == True %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mon') %}

readycheck before processing {{ host }}:
  salt.runner:
    - name: minions.ready
    - timeout: {{ salt['pillar.get']('ready_timeout', 300) }}
    - exception: True
    - failhard: True

upgrading mon on {{ host }}:
  salt.runner:
    - name: minions.message
    - content: "Upgrading mon on host {{ host }}"

wait until the cluster has recovered before processing mon on {{ host }}:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait
    - failhard: True

# OSDs are up and running althouth officially not starting because a missing flag..
check if all processes are still running after processing mon on {{ host }}:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - sls: ceph.processes
    - failhard: True

updating mon {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.upgrade
    - failhard: True

restart mon {{ host }} if updates require:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.mon.restart
    - failhard: True

upgraded mon on {{ host }}:
  salt.runner:
    - name: minions.message
    - content: "Upgraded mon on host {{ host }}"

{% endfor %}

{% for host in salt.saltutil.runner('orderednodes.unique', cluster='ceph', exclude=['mon']) %}

readycheck for {{ host }} after processing mons :
  salt.runner:
    - name: minions.ready
    - timeout: {{ salt['pillar.get']('ready_timeout', 300) }}
    - exception: True
    - failhard: True

upgrading {{ host }}:
  salt.runner:
    - name: minions.message
    - content: "Upgrading host {{ host }}"

# wait until the OSDs/MONs are acutally marked as down ~30 seconds ~1m
wait for ceph to mark services as out/down to process {{ host }}:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait.until.expired.30sec

wait until the cluster has recovered before processing {{ host }}:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait
    - failhard: True

check if all processes are still running after processing {{ host }}:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - sls: ceph.processes
    - failhard: True

unset noout after processing {{ host }}:
  salt.state:
    - sls: ceph.noout.unset
    - tgt: {{ master }}
    - failhard: True

updating {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.upgrade
    - failhard: True

set noout {{ host }}: 
  salt.state:
    - sls: ceph.noout.set
    - tgt: {{ master }}
    - failhard: True

restart {{ host }} if updates require:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.updates.restart
    - failhard: True

upgraded {{ host }}:
  salt.runner:
    - name: minions.message
    - content: "Upgraded host {{ host }}"

{% endfor %}

unset noout after final iteration: 
  salt.state:
    - sls: ceph.noout.unset
    - tgt: {{ master }}
    - failhard: True

set luminous osds: 
  salt.state:
    - sls: ceph.setosdflags.requireosdrelease
    - tgt: {{ master }}
    - failhard: True

{% else %}

{% set notice = salt['saltutil.runner']('advise.no_cluster_detected') %}

{% endif %}

{% else %}

minions not ready:
  test.nop
{% endif %}

