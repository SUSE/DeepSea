{% set master = salt['pillar.get']('master_minion') %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mon') %}

    wait until {{ host }} with role mon can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait

    check if all processes are still running on {{ host }} after restarting mons:
      salt.state:
        - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
        - tgt_type: compound
        - sls: ceph.processes
        - failhard: True

    restarting mons on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.mon.restart
        - failhard: True

{% endfor %}
