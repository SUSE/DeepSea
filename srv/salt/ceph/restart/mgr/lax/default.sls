{% set master = salt['master.minion']() %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mgr') %}

    wait until {{ host }} with role mgr can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait
        - failhard: True

    check if mgr processes are still running on {{ host }} after restarting mgrs:
      salt.state:
        - tgt: 'I@roles:mgr'
        - tgt_type: compound
        - sls: ceph.processes.mgr
        - failhard: True

    restarting mgr on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.mgr.restart
        - failhard: True

{% endfor %}
