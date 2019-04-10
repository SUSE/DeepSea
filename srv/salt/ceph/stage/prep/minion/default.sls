{% set master = salt['master.minion']() %}

crc_method minion:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.salt.crc.minion

repo:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.repo

metapackage minions:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.metapackage

common packages:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.packages.common
    - failhard: True

sync:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.sync

mines:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.mines

{% if salt['saltutil.runner']('cephprocesses.mon') == True %}

#warning_before:
#  salt.state:
#    - tgt: {{ salt['pillar.get']('master_minion') }}
#    - sls: ceph.warning.noout
#    - failhard: True

{% for host in salt.saltutil.runner('orderednodes.unique', cluster='ceph') %}

starting {{ host }}:
  salt.runner:
    - name: minions.message
    - content: "Processing host {{ host }}"

wait until the cluster has recovered before processing {{ host }}:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait
    - failhard: True

check if all processes are still running after processing {{ host }}:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.processes
    - failhard: True

unset noout {{ host }}:
  salt.state:
    - sls: ceph.noout.unset
    - tgt: {{ master }}
    - failhard: True

updating {{ host }}:
  salt.state:
    - tgt: {{ host }}
    - tgt_type: compound
    - sls: ceph.updates
    - failhard: True

set noout {{ host }}:
  salt.state:
    - sls: ceph.noout.set
    - tgt: {{ master }}
    - failhard: True

finished {{ host }}:
  salt.runner:
    - name: minions.message
    - content: "Finished host {{ host }}"

{% endfor %}

unset noout after final iteration:
  salt.state:
    - sls: ceph.noout.unset
    - tgt: {{ master }}
    - failhard: True

starting remaining minions:
  salt.runner:
    - name: minions.message
    - content: "Processing minions without roles"

updating minions without roles:
  salt.state:
    - tgt: I@cluster:ceph
    - tgt_type: compound
    - sls: ceph.updates
    - failhard: True

finishing remaining minions:
  salt.runner:
    - name: minions.message
    - content: "Finished minions without roles"

#warning_after:
#  salt.state:
#    - tgt: {{ salt['pillar.get']('master_minion') }}
#    - sls: ceph.warning.noout
#    - failhard: True

# Here needs to be 100% definitive check that the cluster is not up yet.
# the parent if conditional can be False if one of the mons is down.
# but even if all are down, this is no indication of rebooting/updateing
# all nodes at once
{% else %}

updates:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.updates

{% endif %}
