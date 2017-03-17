# preflight

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

unset noout after processing {{ host }}:
  salt.function:
    - name: cmd.run
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - arg:
      - ceph osd unset noout
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
    - failhard: True

{% endfor %}

# After the last item in the iteration was processed the reactor 
# still sets ceph osd set noout. So setting this after is still necessary.
unset noout after processing all hosts: 
  salt.function:
    - name: cmd.run
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - arg:
      - ceph osd unset noout
    - failhard: True

#postflight
