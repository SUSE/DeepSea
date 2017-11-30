{% set master = salt['pillar.get']('master_minion') %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='openattic') %}

    wait until {{ host }} with role openattic can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait

    check if all processes are still running on {{ host }} after restarting openattic:
      salt.state:
        - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
        - tgt_type: compound
        - sls: ceph.processes
        - failhard: True

    restarting openattic on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.openattic.restart
        - failhard: True

{% endfor %}
