{% for host in salt.saltutil.runner('getnodes.sorted_unique_nodes', cluster='ceph') %}
   
    wait until the cluster is not in a bad state anymore to process {{ host }}:
      salt.state:
        - tgt: {{ salt['pillar.get']('master_minion') }}
        - sls: ceph.wait

    upgrading {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.upgrade
        - failhard: True

{% endfor %}
