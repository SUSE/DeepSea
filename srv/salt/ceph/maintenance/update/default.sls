{% for host in salt.saltutil.runner('select.minions', cluster='ceph') %}

    wait until {{ host }} with role mon can be restarted:
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
