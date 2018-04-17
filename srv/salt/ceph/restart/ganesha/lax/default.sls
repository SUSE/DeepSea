{% set master = salt['master.minion']() %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha') %}
    
    wait until {{ host }} with role ganesha can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait
        - failhard: True

    check if ganesha processes are still running on {{ host }}:
      salt.state:
        - tgt: 'I@roles:ganesha'
        - tgt_type: compound
        - sls: ceph.processes.ganesha
        - failhard: True

    restarting ganesha on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.ganesha.restart
        - failhard: True

{% endfor %}
