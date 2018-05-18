
{% set master = salt['master.minion']() %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') %}

    wait until {{ host }} with role mds can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait
        - failhard: True

    check if all processes are still running on {{ host }} after restarting mdss:
      salt.state:
        - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
        - tgt_type: compound
        - sls: ceph.processes
        - failhard: True

    restarting mds on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.mds.restart
        - failhard: True

{% endfor %}
