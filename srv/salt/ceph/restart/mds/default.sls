{% set master = salt['pillar.get']('master_minion') %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') %}
    
    wait until {{ host }} with role mds can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait

    restarting mds on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.mds.restart
        - failhard: True

{% endfor %}
