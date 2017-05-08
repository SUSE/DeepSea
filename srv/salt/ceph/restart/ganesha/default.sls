{% set master = salt['pillar.get']('master_minion') %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha') %}
    
    wait until {{ host }} with role ganesha can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait

    restarting ganesha on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.ganesha.restart
        - failhard: True

{% endfor %}
